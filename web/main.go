package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var (
	upgrader = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true // Allow all connections
		},
	}
	// Stores the connected Pi clients, should only be one in this case
	clients = make(map[*websocket.Conn]bool)

	ledStates      = make(map[int]string) // map[LED_ID]Color
	ledStatesMutex sync.RWMutex

	ledPositions   = make(map[int]map[string]float32) // map[LED_ID]{"x": x, "y": y, "z": z}
	positionsMutex sync.RWMutex
)

type LightCommand struct {
	Type   string `json:"type"`
	LED    int    `json:"led,omitempty"`
	Color  string `json:"color"`
	Action string `json:"action,omitempty"`
	Name   string `json:"name,omitempty"`
}

type AnimationCommand struct {
	Type   string `json:"type"`
	Action string `json:"action"`
	Name   string `json:"name"`
}

type StatusMessage struct {
	Type    string `json:"type"`
	LED     int    `json:"led"`
	Color   string `json:"color"`
	Success bool   `json:"success"`
}

type LEDStates struct {
	Type   string            `json:"type"`
	States map[string]string `json:"states"`
}

func handleHome(c *gin.Context) {
	c.HTML(http.StatusOK, "index.html", nil)
}

func handleWebSocket(c *gin.Context) {
	// WebSocket handshake with the client
	// Its like "Hello", and "Hello" back, but in a better way
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v\n", err)
		return
	}
	defer conn.Close()

	clients[conn] = true
	defer delete(clients, conn)

	log.Printf("New client connected. Total clients: %d\n", len(clients)) // Total clients should be 1, please don't hack me

	// Handle incoming messages from Pi, which are LED states
	for {
		var msg struct {
			Type      string            `json:"type"`
			States    map[string]string `json:"states,omitempty"`
			LED       int               `json:"led,omitempty"`
			Color     string            `json:"color,omitempty"`
			Positions string            `json:"positions"`
		}
		err := conn.ReadJSON(&msg)
		if err != nil {
			log.Printf("Error reading message: %v\n", err)
			break
		}

		switch msg.Type {
		case "states":
			// Broadcast LED states to all web clients
			log.Printf("Received LED states: %+v\n", msg.States)
			for client := range clients {
				if client != conn { // Don't send back to sender
					err := client.WriteJSON(msg)
					if err != nil {
						log.Printf("Error sending states to client: %v\n", err)
					}
				}
			}
		case "status":
			log.Printf("Received status from client: LED %d = %s\n", msg.LED, msg.Color)

		case "positions":
			var positions []struct {
				ID int     `json:"id"`
				X  float32 `json:"x"`
				Y  float32 `json:"y"`
				Z  float32 `json:"z"`
			}
			if err := json.Unmarshal([]byte(msg.Positions), &positions); err != nil {
				log.Printf("Error parsing positions: %v\n", err)
				break
			}

			positionsMutex.Lock()
			for _, pos := range positions {
				ledPositions[pos.ID] = map[string]float32{
					"x": pos.X,
					"y": pos.Y,
					"z": pos.Z,
				}
			}
			positionsMutex.Unlock()

			// Broadcast positions to all web clients
			for client := range clients {
				if client != conn {
					err := client.WriteJSON(map[string]interface{}{
						"type":      "positions",
						"positions": msg.Positions,
					})
					if err != nil {
						log.Printf("Error sending positions to client: %v\n", err)
					}
				}
			}
		}
	}
}

func handleLightUpdate(c *gin.Context) {
	var cmd LightCommand
	if err := c.BindJSON(&cmd); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	switch cmd.Type {
	case "update":
		// Validate LED index
		// We have 40 LEDs, indexed from 0 to 39
		if cmd.LED < 0 || cmd.LED >= 40 {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid LED index"})
			return
		}

		// Store the LED state
		ledStatesMutex.Lock()
		ledStates[cmd.LED] = cmd.Color
		ledStatesMutex.Unlock()

	case "updateAll":
		// Update all LEDs to the same color
		ledStatesMutex.Lock()
		for i := 0; i < 40; i++ {
			ledStates[i] = cmd.Color
		}
		ledStatesMutex.Unlock()

	case "animation":
		for client := range clients {
			err := client.WriteJSON(cmd)
			if err != nil {
				log.Printf("Error sending to client: %v\n", err)
				delete(clients, client)
				client.Close()
				continue
			}
		}
		c.JSON(http.StatusOK, gin.H{"success": true})
		return

	default:
		c.JSON(http.StatusBadRequest, gin.H{"error": "Unknown command type"})
		return
	}

	// Broadcast to all connected Pis
	for client := range clients {
		err := client.WriteJSON(cmd)
		if err != nil {
			log.Printf("Error sending to client: %v\n", err)
			delete(clients, client)
			client.Close()
			continue
		}
	}

	log.Printf("Sent command to client: %+v\n", cmd)

	c.JSON(http.StatusOK, gin.H{"success": true})
}

// Get LED states
func handleGetStates(c *gin.Context) {
	ledStatesMutex.RLock()
	defer ledStatesMutex.RUnlock()
	c.JSON(http.StatusOK, ledStates)
	fmt.Println(ledStates)
}

func main() {
	r := gin.Default()

	// Give the people the static files
	// r.Static("/static", "./static")
	r.LoadHTMLGlob("templates/*")

	// Routes
	r.GET("/", handleHome)
	r.GET("/ws", handleWebSocket)
	r.POST("/api/updateLights", handleLightUpdate)
	r.GET("/api/getStates", handleGetStates)

	log.Println("Server starting on port 80...")
	r.Run(":80")
}
