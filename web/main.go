package main

import (
	"net/http"

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
)

type LightCommand struct {
	Type  string `json:"type"`
	LED   int    `json:"led,omitempty"`
	Color string `json:"color,omitempty"`
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

	r.Run(":80")
}

func handleHome(c *gin.Context) {
	c.HTML(http.StatusOK, "index.html", nil)
}

func handleWebSocket(c *gin.Context) {
	conn, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer conn.Close()

	clients[conn] = true
	defer delete(clients, conn)

	// Handle incoming messages from Pi
	for {
		var msg LightCommand
		err := conn.ReadJSON(&msg)
		if err != nil {
			break
		}
		// Handle status updates from Pi
	}
}

func handleLightUpdate(c *gin.Context) {
	var cmd LightCommand
	if err := c.BindJSON(&cmd); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Broadcast command to all connected Pis
	for client := range clients {
		err := client.WriteJSON(cmd)
		if err != nil {
			delete(clients, client)
			client.Close()
		}
	}

	c.JSON(http.StatusOK, gin.H{"success": true})
}
