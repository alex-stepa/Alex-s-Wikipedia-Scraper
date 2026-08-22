# chat-app

Vlastní real-time chat server v Rustu. Žádné existující řešení (ne Matrix, ne
XMPP, ne komerční SaaS) — píše se od nuly, fázově.

## Aktuální fáze
Fáze 1 — základní WebSocket echo server.

## Tech stack
- Rust, axum, tokio
- Později: SQLite/sqlx pro perzistenci, JWT pro auth — zatím nepoužito

## Konvence
- Spouštění: `cargo run`
- Testování: websocat nebo python websockets skript proti běžícímu serveru
- Žádné zbytečné dependencies navíc bez zeptání

## Fáze
- [ ] Fáze 1: WebSocket echo (aktuální)
- [ ] Fáze 2: Místnosti/kanály, broadcast mezi klienty
- [ ] Fáze 3: Perzistence zpráv (SQLite)
- [ ] Fáze 4: Autentizace (token-based)
- [ ] Fáze 5: Klient (web UI nebo CLI)

## Poznámka
Vyvíjí se lokálně na Macu, později přesun na Raspberry Pi 5. Žádný kód
závislý na konkrétní architektuře nebo OS.
