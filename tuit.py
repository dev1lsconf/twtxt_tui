import subprocess
from pathlib import Path
from textual import events
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static, Button, Input
from textual.containers import Container, ScrollableContainer
from textual.reactive import reactive
from textual.screen import ModalScreen

class TwtxtTUI(App):
    CSS_PATH = "twtxt_tui.tcss"
    BINDINGS = [
        ("q", "quit", "Salir"),
        ("r", "refresh", "Actualizar"),
        ("p", "post_tweet", "Publicar"),
        ("a", "add_follower", "Seguir")
    ]

    timeline_content = reactive("")

    def compose(self) -> ComposeResult:
        yield Header()
        yield TimelineContainer(Static(id="timeline"), id="timeline_container")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "twtxt TUI"
        self.sub_title = "Microblogging descentralizado"
        self.refresh_timeline()
        self.query_one(TimelineContainer).focus()

    def refresh_timeline(self) -> None:
        try:
            result = subprocess.run(
                ["twtxt", "timeline"],
                capture_output=True,
                text=True,
                check=True
            )
            self.timeline_content = result.stdout
        except subprocess.CalledProcessError as e:
            self.timeline_content = f"Error al actualizar: {e.stderr}"
        except FileNotFoundError:
            self.timeline_content = "Error: twtxt no está instalado"
    
    def action_refresh(self) -> None:
        self.refresh_timeline()

    def watch_timeline_content(self, content: str) -> None:
        self.query_one("#timeline", Static).update(content)

    async def action_post_tweet(self) -> None:
        async def handle_tweet(content: str | None) -> None:
            if content:
                try:
                    subprocess.run(["twtxt", "tweet", content], check=True)
                    self.refresh_timeline()
                except subprocess.CalledProcessError as e:
                    self.notify(f"Error: {e.stderr}", severity="error")

        await self.push_screen(InputModal("Escribe tu tweet:"), handle_tweet)

    async def action_add_follower(self) -> None:
        async def handle_follower(data: tuple | None) -> None:
            if data:
                nickname, url = data
                try:
                    subprocess.run(["twtxt", "follow", nickname, url], check=True)
                    self.notify(f"Ahora sigues a {nickname}!", severity="success")
                    self.refresh_timeline()
                except subprocess.CalledProcessError as e:
                    self.notify(f"Error: {e.stderr}", severity="error")

        await self.push_screen(FollowModal(), handle_follower)

class TimelineContainer(ScrollableContainer):
    BORDER_TITLE = "Timeline (↑/↓/PgUp/PgDn para navegar)"
    
    async def key_up(self, event: events.Key) -> None:
        self.scroll_relative(y=-1, animate=False)
    
    async def key_down(self, event: events.Key) -> None:
        self.scroll_relative(y=1, animate=False)
    
    async def key_page_up(self, event: events.Key) -> None:
        self.scroll_page_up()
    
    async def key_page_down(self, event: events.Key) -> None:
        self.scroll_page_down()
    
    async def key_k(self, event: events.Key) -> None:
        self.scroll_relative(y=-1, animate=False)
    
    async def key_j(self, event: events.Key) -> None:
        self.scroll_relative(y=1, animate=False)

class InputModal(ModalScreen[str]):
    def __init__(self, prompt: str) -> None:
        super().__init__()
        self.prompt = prompt

    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.prompt, classes="prompt"),
            Input(placeholder="Escribe aquí...", id="input"),
            Button("Enviar", variant="primary", id="submit"),
            classes="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            self.dismiss(self.query_one("#input", Input).value)

class FollowModal(ModalScreen[tuple]):
    def compose(self) -> ComposeResult:
        yield Container(
            Static("Añadir nuevo seguido:", classes="prompt"),
            Input(placeholder="Nickname", id="nickname"),
            Input(placeholder="URL", id="url"),
            Button("Seguir", variant="primary", id="submit"),
            classes="dialog"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit":
            nickname = self.query_one("#nickname", Input).value
            url = self.query_one("#url", Input).value
            self.dismiss((nickname, url))

if __name__ == "__main__":
    config_path = Path.home() / ".config" / "twtxt" / "config"
    if not config_path.exists():
        print("Primero configura twtxt: twtxt config")
        exit(1)

    app = TwtxtTUI()
    app.run()
