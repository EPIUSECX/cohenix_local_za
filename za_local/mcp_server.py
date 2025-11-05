from frappe_mcp.server.server import MCP


# Expose an MCP server for development.
# Name it "frappe-workspace" so MCP clients can list it as installed.
mcp = MCP(name="frappe-workspace")


@mcp.register(allow_guest=True, xss_safe=True)
def mcp_endpoint():
	# Import tool modules here if/when you add them.
	# For now, the server exposes core MCP methods with an empty tool registry.
	return


