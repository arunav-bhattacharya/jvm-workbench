from fg import *
import fg
import bisect

fg.SAY[:0] = [(r"\bms\b", "milliseconds"), (r"\b1 MB\b", "one megabyte"), (r"\bMB\b", "megabytes"), (r"\bGB\b", "gigabytes"),
              (r"\b64-bit\b", "sixty-four bit"), (r"\b1\.28\b", "one point two eight")]


# ---- helpers for this file ----
def code(lines, size=26, color=WHITE, ls=0.6):
    """Monospace block that keeps indentation. Returns a VGroup with one sub-group per line."""
    t = Text("\n".join(lines), font=MONO, font_size=size, color=color, line_spacing=ls)
    out, i = VGroup(), 0
    for ln in lines:
        n = len(ln.replace(" ", ""))
        out.add(VGroup(*t[i:i + n]))
        i += n
    return out


def titled(label, block, buff=0.18):
    return VGroup(T(label, 22, GREY_B), block).arrange(DOWN, aligned_edge=LEFT, buff=buff)


def seq(scene, text, *steps, after=0.25):
    """Speak one line and play several animation groups one after another inside it."""
    path, dur = voice(text)
    scene._cue(text, dur)
    scene.add_sound(path)
    used = 0
    for st in steps:
        if isinstance(st, (int, float)):
            scene.wait(st); used += st
        else:
            anims, rt = st
            if callable(anims):
                anims = anims()
            if rt is None:                       # stretch this step to the end of the line
                rt = max(0.5, dur - used - 0.1)
            scene.play(*anims, run_time=rt); used += rt
    if dur - used > 0.02:
        scene.wait(dur - used)
    if after:
        scene.wait(after)


def dark(color, k=0.14):
    return interpolate_color(ManimColor("#000000"), ManimColor(color), k)


def counter(fmt, fn, pos, size=30, color=WHITE, edge=ORIGIN):
    """Text that shows fmt.format(fn()); it changes in place with become(), so no stale copy is ever drawn."""
    cache = {}

    def get(n):
        if n not in cache:
            cache[n] = T(fmt.format(n), size, color).move_to(pos, aligned_edge=edge)
        return cache[n]
    n0 = fn()
    holder = get(n0).copy()
    holder.shown = n0

    def upd(m):
        n = fn()
        if n != m.shown:
            m.become(get(n))
            m.shown = n
    holder.add_updater(upd)
    return holder


def stage_bar(issuer_ms, x0, x1, y, h, min_w=0.0):
    """One request as five blocks: parse, fraud, issuer, ledger, reply. Gold = CPU, grey = waiting."""
    parts = [(2, GOLD_M), (40, GREY_M), (issuer_ms, GREY_M), (35, GREY_M), (3, GOLD_M)]
    total = sum(p for p, _ in parts)
    widths = [max(min_w, (x1 - x0) * p / total) for p, _ in parts]
    k = (x1 - x0) / sum(widths)
    g, x = VGroup(), x0
    for (p, c), w in zip(parts, widths):
        w *= k
        r = Rectangle(width=w, height=h, stroke_color=BLACK, stroke_width=2)
        r.set_fill(c if c == GOLD_M else dark(GREY_M, 0.55), 1).move_to([x + w / 2, y, 0])
        g.add(r)
        x += w
    return g


# ---- the pool simulation: 200 threads, FIFO queue, each request holds its thread for W ms ----
N_THREADS = 200
T_UP = 600.0          # traffic rises from 800 to 1,500 a second here (sim ms)


def simulate(t_slow, t_end):
    arr, t = [], -700.0
    while t < t_end:
        arr.append(t)
        t += 1000.0 / (800.0 if t < T_UP else 1500.0)
    free_at = [-1e9] * N_THREADS
    starts, ends, tid, prev = [], [], [], -1e9
    for a in arr:
        t0 = max(a, prev)
        i = next((j for j in range(N_THREADS) if free_at[j] <= t0), None)
        if i is None:
            t0 = min(free_at)
            i = next(j for j in range(N_THREADS) if free_at[j] <= t0)
        e = t0 + (200.0 if t0 < t_slow else 1280.0)
        free_at[i] = e
        starts.append(t0); ends.append(e); tid.append(i); prev = t0
    cs = [[] for _ in range(N_THREADS)]
    ce = [[] for _ in range(N_THREADS)]
    for s, e, i in zip(starts, ends, tid):
        cs[i].append(s); ce[i].append(e)
    return arr, starts, sorted(ends), cs, ce


