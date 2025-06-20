# MC Server Holder

A lightweight Minecraft server that keeps a port open and displays a customizable MOTD & kick message when the main server is offline.

## Features

- **Centered MOTD**: Pixel-perfect centering based on actual character widths
- **Color Code Support**: Compatible with all Minecraft formatting codes (`§`)
- **Connection Management**: Proper responses to status requests and login attempts
- **Flexible Configuration**: TOML file for easy configuration
- **Customizable Messages**: Configurable MOTD and disconnect messages
- **No Dependencies**: Pure Python implementation with no external libraries required. Plug-and-play setup.
- **Cross-Platform**: Works on Windows, Linux, and macOS

## Installation

1. Clone the repository:
```bash
git clone <repo-url>
cd mc-server-holder
```

2. Ensure you have Python 3.6+ installed

3. The project requires no external dependencies

## Configuration

Edit `config/config.toml` to customize your server:

```toml
[server]
host = "0.0.0.0"
port = 25565

[server.messages.motd]
line_1 = "§6§lMY SERVER"
line_2 = "§cServer is closed for §c§lMAINTENANCE."
centered = "11"  # "11" = both lines centered

[server.messages]
kick_message = "§cSorry, the server is closed.\n§c§lPlease come back later!"

[minecraft]
version = "Maintenance"
protocol_version = 47 # Recommended for max compatibility
```

### Centering Options

- `"00"` : No lines centered
- `"10"` : First line centered only
- `"01"` : Second line centered only
- `"11"` : Both lines centered

## Usage

### Start the server

```bash
python main.py
```

The server will start on the configured port (25565 by default) and display:
```
[OK] MC Server Holder running on 0.0.0.0:25565
Waiting for connections... Press Ctrl+C to stop.
```

## API

### Server Responses

- **Ping** : Responds with formatted MOTD and server information
- **Login** : Disconnects with a custom message
- **Timeout** : Proper connection handling

### JSON Response Format

```json
{
  "version": {
    "name": "Maintenance",
    "protocol": 47
  },
  "players": {
    "max": 0,
    "online": 0,
    "sample": [""]
  },
  "description": {
    "text": "§6§lMY SERVER\n§cServer is closed for §c§lMAINTENANCE."
  }
}
```

## Compatibility

- **Python** : 3.6+
- **Minecraft** : All versions (adjustable protocol)
- **OS** : Windows, Linux, macOS

## Troubleshooting

### Port already in use
```
[ERROR] Port 25565 may be already in use
```
Change the port in `config/config.toml` or stop the main Minecraft server.

### Missing configuration file
The server will use default configuration if `config/config.toml` is missing.

### Incorrect centering
Verify that `data/fontWidths.txt` exists and contains character widths.

## License

MIT License - See LICENSE file for details.
