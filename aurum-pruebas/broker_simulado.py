"""Broker MT5 simulado con velas reales (datos.db). Imita la API de MetaTrader5 que usan los bots de Aurum."""
import sqlite3
from types import SimpleNamespace as NS

ACCOUNT_TRADE_MODE_DEMO, ACCOUNT_TRADE_MODE_REAL = 0, 2
DEAL_ENTRY_IN, DEAL_ENTRY_OUT = 0, 1
DEAL_TYPE_BUY, DEAL_TYPE_SELL = 0, 1
POSITION_TYPE_BUY, POSITION_TYPE_SELL = 0, 1
ORDER_TYPE_BUY, ORDER_TYPE_SELL = 0, 1
ORDER_FILLING_FOK, ORDER_FILLING_IOC, ORDER_FILLING_RETURN = 0, 1, 2
ORDER_TIME_GTC = 0
TRADE_ACTION_DEAL, TRADE_ACTION_SLTP = 1, 6
TRADE_RETCODE_DONE = 10009
TIMEFRAME_H1, TIMEFRAME_D1 = 16385, 16408
DUR = {TIMEFRAME_H1: 3600, TIMEFRAME_D1: 86400}
TFN = {TIMEFRAME_H1: "H1", TIMEFRAME_D1: "D1"}
# valor por 1.0 de precio por lote = tick_value / tick_size
SPEC = {"XAUUSD": (1.0, 0.01, 0.01, 0.01), "US500": (0.01, 0.01, 0.1, 0.1), "ETHUSD": (0.01, 0.01, 0.1, 0.1),
        "GER40": (0.01, 0.01, 0.1, 0.1), "US2000": (0.01, 0.01, 0.1, 0.1), "BTCUSD": (0.01, 0.01, 0.1, 0.1), "USTECH": (0.01, 0.01, 0.1, 0.1), "US30": (0.01, 0.01, 0.1, 0.1)}


class Broker:
    def __init__(self, db, login, balance, offset_h=2, trade_mode=0):
        self.login, self.balance, self.offset, self.trade_mode = login, balance, offset_h * 3600, trade_mode
        con = sqlite3.connect(db)
        self.data = {}
        for s, tf, t, o, h, l, c, sp in con.execute("SELECT * FROM velas ORDER BY time"):
            self.data.setdefault((s, tf), []).append((t, o, h, l, c, sp))
        con.close()
        self.T = 0
        self.pos, self.deals, self.n = {}, [], 1000
        self.trade_allowed = True
        self.ultimo_proceso = {}

    # --- reloj y ejecución de SL/TP ---
    def fino(self, s):
        return (s, "H1") if (s, "H1") in self.data else (s, "D1")

    def avanzar(self, T):
        """Mueve el reloj a T (UTC) y ejecuta los SL/TP tocados por las velas que cerraron entre el reloj anterior y T."""
        for p in list(self.pos.values()):
            k = self.fino(p.symbol)
            dur = 3600 if k[1] == "H1" else 86400
            for b in self.data[k]:
                fin = b[0] + dur
                # una vela diaria cuenta aunque la entrada fuera unas horas después de su apertura (las entradas D1 se hacen al abrir)
                if fin <= self.T or fin > T or b[0] + (6 * 3600 if dur == 86400 else 0) < p.t_utc:
                    continue
                compra = p.type == 0
                if p.sl and ((compra and b[3] <= p.sl) or (not compra and b[2] >= p.sl)):
                    self._cerrar(p, p.sl, fin, "sl")
                    break
                if p.tp and ((compra and b[2] >= p.tp) or (not compra and b[3] <= p.tp)):
                    self._cerrar(p, p.tp, fin, "tp")
                    break
        self.T = T

    def _barra_actual(self, s):
        k = self.fino(s)
        if k not in self.data:
            return None
        dur = 3600 if k[1] == "H1" else 86400
        cerradas = [b for b in self.data[k] if b[0] + dur <= self.T]
        return cerradas[-1] if cerradas else None

    def spec(self, s):
        """(valor por 1.0 de precio por lote, lote mínimo) con aproximaciones razonables para los mercados sin ficha."""
        if s in SPEC:
            tv, ts, vmin, _ = SPEC[s]
            return tv / ts, vmin
        b = self._barra_actual_raw(s)
        p = b[4] if b else 1.0
        if len(s) == 6 and s.isalpha():                      # divisas: contrato de 100,000
            if s.endswith("USD"):
                return 100000.0, 0.01
            if s.endswith("JPY"):
                return 100000.0 / 155.0, 0.01
            return 100000.0 / p if s.startswith("USD") else 100000.0 / 1.3, 0.01
        if s == "XAGUSD":
            return 5000.0, 0.01
        if s == "XPTUSD":
            return 100.0, 0.01
        return 1.0, 0.01                                      # índices, cripto, energía: $1 por punto

    def _barra_actual_raw(self, s):
        k = (s, "D1")
        if k not in self.data:
            return None
        c = [b for b in self.data[k] if b[0] + 86400 <= self.T]
        return c[-1] if c else None

    def vpp(self, s):
        return self.spec(s)[0]

    def _cerrar(self, p, precio, t, motivo):
        d = 1 if p.type == 0 else -1
        profit = (precio - p.price_open) * d * self.vpp(p.symbol) * p.volume
        self.balance += profit
        self.n += 1
        self.deals.append(NS(ticket=self.n, order=self.n, position_id=p.ticket, time=int(t + self.offset), type=1 - p.type, entry=DEAL_ENTRY_OUT,
                             magic=p.magic, symbol=p.symbol, volume=p.volume, price=precio, profit=profit, swap=0.0, commission=0.0, comment=motivo))
        del self.pos[p.ticket]

    # --- API MetaTrader5 ---
    def initialize(self, path=None, **k): return True
    def shutdown(self): pass
    def last_error(self): return (1, "Success")
    def symbol_select(self, s, v=True): return any(k[0] == s for k in self.data)

    def terminal_info(self): return NS(connected=True, trade_allowed=self.trade_allowed)

    def account_info(self):
        flot = sum(p.profit for p in self.positions_get())
        return NS(login=self.login, trade_mode=self.trade_mode, balance=self.balance, equity=self.balance + flot, currency="USD", margin_free=self.balance)

    def symbol_info(self, s):
        if not self.symbol_select(s):
            return None
        v, vmin = self.spec(s)
        return NS(trade_tick_value=v * 0.00001, trade_tick_size=0.00001, volume_min=vmin, volume_step=vmin, volume_max=100.0, digits=5, point=0.00001, filling_mode=1)

    def symbol_info_tick(self, s):
        b = self._barra_actual(s)
        if b is None:
            return None
        return NS(bid=b[4], ask=b[4] + max(b[5], 0.01), time=int(self.T + self.offset), last=b[4])

    def copy_rates_from_pos(self, s, tf, start, count):
        k = (s, TFN[tf])
        if k not in self.data:
            return None
        cerradas = [b for b in self.data[k] if b[0] + DUR[tf] <= self.T]
        sel = cerradas[-count:] if start == 1 else cerradas[-count - start + 1:len(cerradas) - start + 1]
        return [{"time": b[0] + self.offset, "open": b[1], "high": b[2], "low": b[3], "close": b[4], "spread": 0, "tick_volume": 0} for b in sel]

    def positions_get(self, symbol=None, ticket=None, **k):
        out = []
        for p in self.pos.values():
            if (symbol and p.symbol != symbol) or (ticket and p.ticket != ticket):
                continue
            t = self.symbol_info_tick(p.symbol)
            precio = t.bid if p.type == 0 else t.ask
            p.profit = (precio - p.price_open) * (1 if p.type == 0 else -1) * self.vpp(p.symbol) * p.volume
            out.append(p)
        return out

    def history_deals_get(self, desde, hasta, **k):
        import datetime as _dt
        a = desde.replace(tzinfo=_dt.timezone.utc).timestamp()
        if abs(a - _dt.datetime.now(_dt.timezone.utc).timestamp()) < 3 * 86400:  # "hoy" real → hoy simulado
            a = self.T - self.T % 86400
        return [d for d in self.deals if d.time - self.offset >= a]

    def order_send(self, r):
        t = self.symbol_info_tick(r["symbol"])
        if r["action"] == TRADE_ACTION_SLTP:
            p = self.pos.get(r["position"])
            if p:
                p.sl, p.tp = r.get("sl", 0.0), r.get("tp", 0.0)
            return NS(retcode=TRADE_RETCODE_DONE, order=r["position"], price=0)
        if "position" in r:
            p = self.pos.get(r["position"])
            if not p:
                return NS(retcode=10013, order=0, price=0)
            precio = t.bid if p.type == 0 else t.ask
            self._cerrar(p, precio, self.T, r.get("comment", ""))
            return NS(retcode=TRADE_RETCODE_DONE, order=self.n, price=precio)
        precio = t.ask if r["type"] == 0 else t.bid
        self.n += 1
        p = NS(ticket=self.n, symbol=r["symbol"], type=r["type"], volume=r["volume"], price_open=precio, sl=r.get("sl", 0.0),
               tp=r.get("tp", 0.0), magic=r.get("magic", 0), time=int(self.T + self.offset), t_utc=self.T, profit=0.0, swap=0.0, comment=r.get("comment", ""))
        self.pos[p.ticket] = p
        self.deals.append(NS(ticket=self.n, order=self.n, position_id=self.n, time=int(self.T + self.offset), type=r["type"], entry=DEAL_ENTRY_IN,
                             magic=p.magic, symbol=p.symbol, volume=p.volume, price=precio, profit=0.0, swap=0.0, commission=0.0, comment=p.comment))
        return NS(retcode=TRADE_RETCODE_DONE, order=self.n, price=precio)
