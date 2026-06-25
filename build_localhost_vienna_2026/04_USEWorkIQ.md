```
npx @microsoft/workiq@latest -h 
npx @microsoft/workiq@latest accept-eula
npx @microsoft/workiq@latest logout 

npx @microsoft/workiq@latest ask -q  "ich suche eine email vom stromleiferanten verbund"
```

.vs-code/mcp.json

```json
{
  "my-mcp-server-workiq": {
        "type": "stdio",
        "command": "/Users/pkirschner/.nvm/versions/node/v22.14.0/bin/npx",
        "args": ["-y", "@microsoft/workiq@latest", "mcp"]
	}
}
```

Show in VS Code Copilot UI!!!