package main

import (
	"log"
	"net/http"
	"sync"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
)

var (
	upgrader = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true // Allow all connections in dev
		},
	}
	// Stores the connected Pi clients, should only be one in this case
	clients = make(map[*websocket.Conn]bool)
	// Add LED states storage
	ledStates      = make(map[int]string) // map[LED_ID]Color
	ledStatesMutex sync.RWMutex
)

type LightCommand struct {
	Type  string `json:"type"`
	LED   int    `json:"led"`
	Color string `json:"color"`
}

type StatusMessage struct {
	Type    string `json:"type"`
	LED     int    `json:"led"`
	Color   string `json:"color"`
	Success bool   `json:"success"`
}

// Add new type for LED states
type LEDStates struct {
	Type   string            `json:"type"`
	States map[string]string `json:"states"`
}

func handleHome(c *gin.Context) {
	c.HTML(http.StatusOK, "index.html", nil)
}

// Update handleWebSocket function:
func handleWebSocket(c *gin.Context) {
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v\n", err)
		return
	}
	defer conn.Close()

	clients[conn] = true
	defer delete(clients, conn)

	log.Printf("New client connected. Total clients: %d\n", len(clients)) // Total clients should be 1

	// Handle incoming messages from Pi, which are LED states
	for {
		var msg struct {
			Type   string            `json:"type"`
			States map[string]string `json:"states,omitempty"`
			LED    int               `json:"led,omitempty"`
			Color  string            `json:"color,omitempty"`
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
		}
	}
}

func handleLightUpdate(c *gin.Context) {
	var cmd LightCommand
	if err := c.BindJSON(&cmd); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Validate LED index
	if cmd.LED < 0 || cmd.LED >= 20 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid LED index"})
		return
	}

	// Store the LED state
	ledStatesMutex.Lock()
	ledStates[cmd.LED] = cmd.Color
	ledStatesMutex.Unlock()

	// Broadcast command to all connected Pis
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
}

// Add new handler to get LED states
func handleGetStates(c *gin.Context) {
	ledStatesMutex.RLock()
	defer ledStatesMutex.RUnlock()
	c.JSON(http.StatusOK, ledStates)
}

func main() {
	r := gin.Default()

	// Serve static files
	r.Static("/static", "./static")
	r.LoadHTMLGlob("templates/*")

	// Routes
	r.GET("/", handleHome)
	r.GET("/ws", handleWebSocket)
	r.POST("/api/lights", handleLightUpdate)
	r.GET("/api/states", handleGetStates) // Add new endpoint

	log.Println("Server starting on port 80...")
	r.Run(":80")
}
