package main

import (
	"log"

	"github.com/mark3labs/mcp-go/server"
	"github.com/seekrays/mcp-monitor/cpu"
	"github.com/seekrays/mcp-monitor/disk"
	"github.com/seekrays/mcp-monitor/host"
	"github.com/seekrays/mcp-monitor/memory"
	"github.com/seekrays/mcp-monitor/network"
	"github.com/seekrays/mcp-monitor/process"
)

func main() {
	log.Println("Initializing MCP System Monitor...")
	
	// Create MCP server
	s := server.NewMCPServer(
		"System Monitor",
		"1.0.0",
	)
	log.Println("Created MCP server instance")

	// Add CPU tool
	log.Println("Adding CPU tool...")
	s.AddTool(cpu.NewTool(), cpu.Handler)

	// Add memory tool
	log.Println("Adding memory tool...")
	s.AddTool(memory.NewTool(), memory.Handler)

	// Add disk tool
	log.Println("Adding disk tool...")
	s.AddTool(disk.NewTool(), disk.Handler)

	// Add network tool
	log.Println("Adding network tool...")
	s.AddTool(network.NewTool(), network.Handler)

	// Add host tool
	log.Println("Adding host tool...")
	s.AddTool(host.NewTool(), host.Handler)

	// Add process tool
	log.Println("Adding process tool...")
	s.AddTool(process.NewTool(), process.Handler)

	// Start the stdio server
	log.Println("Starting MCP System Monitor server...")
	if err := server.ServeStdio(s); err != nil {
		log.Printf("Server error: %v\n", err)
	}
} 