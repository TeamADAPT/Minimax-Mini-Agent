#Crew Online Six-Way

## Objective

Extend visible TUI + NATS bridge coverage to all six crew novas (Iris, Zap, Forge, Synergy, Tecton, plus standing Echo/Skipper). Each nova gets a dedicated `nova.<name>.direct` subject, a bridge service, and a GNOME terminal with xdotool class.

## Owner

Zap (with Iris routing support)

## Dependencies

None for scaffold; Task 36+ need this to publish or receive.

## Steps

1. Create systemd service template from echo/skipper bridge, parametrize by nova name
2. Add nova-to-window-class mapping to scripts/crew_nova_config.py
3. Launch 4 new TUI sessions (echo/skipper already live)
4. Fire 5 reachable visible pings per new nova


## Acceptance

All six `nova.<name>.direct` subjects return unique pong from a fresh ping; no two novas share a window class; systemd --user status green for every bridge.

## Rollback

systemctl --user stop <new-bridge>.service; no existing live subject ownership changed.
