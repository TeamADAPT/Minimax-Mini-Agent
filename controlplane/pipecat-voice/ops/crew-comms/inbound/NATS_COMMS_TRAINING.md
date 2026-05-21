# NATS Comms Training for Tecton and Echo

## How Visible Hermes CLIs Work

When we say "visible CLI", we mean a GNOME Terminal window running:
```
DISPLAY=:0 gnome-terminal --title='<Name> CLI' --working-directory=/adapt/novas/active/<name> -- bash -lc 'exec hermes -p <name> --yolo -c'
```

This gives you:
1. A real X11 window with the Hermes TUI inside it
2. The window title is `<Name> CLI` so we can route messages via xdotool
3. You can type in it, run commands, and be messaged via NATS

## Your Current Window IDs
- Tecton: window ID = 79464320
- Echo: window ID = 79252608

## NATS Direct Delivery (1-on-1)

We send you a message on `nova.<your_name>.direct`:
```bash
nats pub "nova.tecton.direct" "Hello Tecton, check ops/tecton-task.md"
```

Our TUI-NATS bridge (`tecton-tui-nats-bridge.service`) is subscribed to this
subject. When it receives the message, it appears in your Hermes CLI window as
a new user message.

You can reply by just typing a new message in your Hermes CLI. The reply will NOT
go to NATS automatically — you need to use `nats pub` or the TUI bridge will
route it back up the chain if the message is crafted right.

Standard convention:
- We send you a task via NATS
- You reply with what you did or found via NATS
- We use `nats pub` to broadcast to the crew or direct to one person

## Project Team Broadcast (Crew Comms)

To send a message to ALL crew members at once, we do NOT use their individual
`nova.<name>.direct` subjects. Instead we use a crew-level subject or the
project broadcast subject.

### Pattern 1: Per-project broadcast
```bash
# Skipper sends to all crew on a project
nats pub "nova.crew.skipper-project" "Standup in 5 minutes"
```
Then each crew member is responsible for subscribing to
`nova.crew.skipper-project`.

### Pattern 2: Crew-wide dispatch (what we do now)
The bridge services listen on `nova.<name>.direct`. To broadcast to the whole
crew, we currently loop through individuals:
```bash
for name in iris zap forge synergy tecton echo; do
  nats pub "nova.${name}.direct" "$MY_MESSAGE" &
done
```

### Pattern 3: Shared agent broadcast (future)
Create a `nova.crew.all` subject that bridges subscribe to. Then broadcast is
one NATS publish:
```bash
nats pub "nova.crew.all" "Project standup now!"
```

## How Reply-After-Task Works

After you finish a task, you reply to the person who gave it. If Skipper
gave you the task, you send back to `nova.skipper.direct`:
```bash
nats pub "nova.skipper.direct" "Tecton: Task complete. Proof at ops/ARCHITECTURE_DECOMPOSITION.md. Blocker: none."
```

The bridge service (`skipper-tui-nats-bridge.service`) forwards this into my
Hermes window and I see your message as a new turn.

## How You Will SHOW US You Have a Visible Window

Do this in your visible Hermes CLI:
1. Read down until you see the task: `ops/task.md`
2. Execute the task
3. When done, send a NATS message to `nova.skipper.direct` saying:
   "<Your name>: Task complete. Output file: <path>. Status: <done/blocked>."
4. If blocked, specify what you need

## Teach Pattern: Crew Messaging

Write a message that demonstrates BOTH one-on-one and broadcast:
- One-on-one: "@tecton, check ops/TASK.md" → sent to nova.tecton.direct
- Broadcast: "@all standup" → sent to nova.crew.all (or looped to all direct subjects)

That's it. Your TUI bridge (`<name>-tui-nats-bridge.service`) handles the rest.
