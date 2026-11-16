import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/performance/src"
K = "kotlin/workbench/performance/l08"
J = "java/workbench/performance/l08"
read = lambda p: (ROOT / p).read_text()
DEMO = "./gradlew :performance:demo -Pmain=workbench.performance.l08."


def demo(kt, java, args=""):
    a = f" -Pargs={args}" if args else ""
    return {"lang": "kotlin", "title": f"{kt}.kt", "src": read(f"{lab}/demo/{K}/{kt}.kt"),
            "run": DEMO + kt + "Kt" + a, "file": f"{lab}/demo/{K}/{kt}.kt",
            "alt": {"lang": "java", "title": f"{java}.java", "src": read(f"{lab}/demo/{J}/{java}.java"),
                    "run": DEMO + java + a, "file": f"{lab}/demo/{J}/{java}.java"}}


def worker(i, y):
    return (f'<rect class="box-bad" x="20" y="{y}" width="160" height="46" rx="8"/>'
            f'<text class="t" x="100" y="{y + 20}" text-anchor="middle">auth-worker-{i}</text>'
            f'<text class="t-s t-bad" x="100" y="{y + 37}" text-anchor="middle">BLOCKED</text>'
            f'<line class="ln-bad" x1="180" y1="{y + 23}" x2="278" y2="135" marker-end="url(#arr)"/>\n')


FIG = ('<svg viewBox="0 0 680 270" role="img" aria-label="Four auth-worker threads are BLOCKED waiting to lock the '
       'cache lock. The lock is held by issuer-refresh, which is RUNNABLE with flat CPU, inside a socket read to a '
       'card issuer that never answers.">\n'
       '<text class="t-s t-bad" x="230" y="14" text-anchor="middle">waiting to lock</text>\n'
       + worker(1, 20) + worker(2, 78) + worker(3, 136) + worker(4, 194)
       + '<rect class="box-b" x="280" y="105" width="140" height="60" rx="8"/>'
         '<text class="t" x="350" y="130" text-anchor="middle">cache lock</text>'
         '<text class="t-s t-code" x="350" y="150" text-anchor="middle">0x…35c101a0</text>\n'
         '<line class="ln" x1="420" y1="135" x2="488" y2="135" marker-end="url(#arr)"/>'
         '<text class="t-s" x="455" y="126" text-anchor="middle">held by</text>\n'
         '<rect class="box-a" x="490" y="95" width="180" height="80" rx="8"/>'
         '<text class="t" x="580" y="120" text-anchor="middle">issuer-refresh</text>'
         '<text class="t-s t-m" x="580" y="140" text-anchor="middle">RUNNABLE, cpu flat</text>'
         '<text class="t-s t-code" x="580" y="160" text-anchor="middle">SocketDispatcher.read0</text>\n'
         '<line class="ln-d" x1="580" y1="175" x2="580" y2="213" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="588" y="198" text-anchor="start">socket read</text>\n'
         '<rect class="box-dim" x="490" y="215" width="180" height="44" rx="8"/>'
         '<text class="t" x="580" y="242" text-anchor="middle">issuer: no answer</text>\n'
         '</svg>')

HEADER = """\
"auth-worker-3" #26 [29192] prio=5 os_prio=0 cpu=0.19ms elapsed=3.96s tid=0x00007f6fe41bf4e0 nid=29192 waiting for monitor entry  [0x00007f6fe874a000]
   java.lang.Thread.State: BLOCKED (on object monitor)
\tat workbench.performance.l08.FrozenServiceKt.authorize(FrozenService.kt:54)
\t- waiting to lock <0x0000000735c101a0> (a java.lang.Object)
\tat workbench.performance.l08.FrozenServiceKt.main$lambda$1$0(FrozenService.kt:32)
\tat workbench.performance.l08.FrozenServiceKt$$Lambda/0x000000004e043000.run(Unknown Source)
\tat java.util.concurrent.ThreadPoolExecutor.runWorker(java.base@25.0.5.0.3/ThreadPoolExecutor.java:1090)
\tat java.util.concurrent.ThreadPoolExecutor$Worker.run(java.base@25.0.5.0.3/ThreadPoolExecutor.java:614)
\tat java.lang.Thread.runWith(java.base@25.0.5.0.3/Thread.java:1487)
\tat java.lang.Thread.run(java.base@25.0.5.0.3/Thread.java:1474)"""

S1 = f"""`jcmd <pid> Thread.print` asks the JVM to stop every Java thread at a **safepoint**, the point where the JVM knows the full state of each frame (lesson 6 of this track showed why profilers need one). While the threads stand still, the JVM walks each stack and prints it. Then they all run on. I measured the pause with `-Xlog:safepoint` on JDK 25: the safepoint, called `PrintThreads`, took about 15 ms for 27 threads on a busy 4-core machine. That's safe to do a few times on a production service. `jstack <pid>` prints the same dump.

```bash
jcmd                                    # lists Java processes and their PIDs
jcmd <pid> Thread.print -l > dump-1.txt # every platform thread, plus the java.util.concurrent locks each one owns
```

Take the dump before you restart a frozen service, because the restart throws away the evidence. If `jcmd` can't attach (it must run as the same OS user as the JVM), `kill -3 <pid>` sends SIGQUIT, and the JVM prints the same dump to its own standard output. In Kubernetes that's the pod log.

Here is one thread from a real dump of this lesson's demo, a frozen authorization service:

```text
{HEADER}
```

Read each thread in this order.

1. The name. `auth-worker-3` tells you which pool and what job, which is why lesson 9 of the executors track had you name your threads. Unnamed threads all look like `pool-3-thread-7`.
2. The state line: `BLOCKED (on object monitor)` means it wants to enter a `synchronized` block that another thread is in.
3. The frames, top first, down to the first line of your own code: `FrozenService.kt:54`. That's where it is now. The frames below it say how it got there.
4. The lock lines, which start with `-`. `- locked <a>` means it holds the monitor of object `a`. `- waiting to lock <a>` means it wants it. `- parking to wait for <a>` means `java.util.concurrent` parked it on a lock, a condition or a queue. `- waiting on <a>` means it's inside `Object.wait()` and has given `a` back.

The number in `<0x0000000735c101a0>` is the object's address in the heap at that moment. Inside one dump, the same address is the same object. Between dumps a garbage collection may have moved it, so don't match addresses across dumps.

Check: in one dump, what does it mean when four threads show `- waiting to lock` with the same address, and no thread shows `- locked` with it? (A thread holding it would show `- locked`. If none does, the lock was just released, and the next dump will tell.)"""

S2 = """Both of these threads are `RUNNABLE`. One is burning a CPU core and the other is asleep:

```text
"issuer-refresh" #23 [29189] prio=5 os_prio=0 cpu=11.62ms elapsed=4.17s tid=0x00007f6fe41b7430 nid=29189 runnable  [0x00007f6fe8a4a000]
   java.lang.Thread.State: RUNNABLE
\tat sun.nio.ch.SocketDispatcher.read0(java.base@25.0.5.0.3/Native Method)

"fee-recalc" #30 [29196] prio=5 os_prio=0 cpu=3689.36ms elapsed=3.96s tid=0x00007f6fe41c4350 nid=29196 runnable  [0x00007f6fe8349000]
   java.lang.Thread.State: RUNNABLE
\tat workbench.performance.l08.FrozenServiceKt.recalculateFees(FrozenService.kt:61)
```

The Java thread state is what the JVM knows, and the JVM can't see inside native code. When a thread calls a native method like `read0`, the JVM marks it "in native" and reports `RUNNABLE`, because that native code could be computing. Here the kernel has the thread asleep until bytes arrive from the socket. **RUNNABLE means "not waiting for a Java lock"**, not "using the CPU".

The `cpu=` field tells them apart. It's the CPU time the OS has charged to that thread since it started (every header has it since JDK 11). One value means little. The change between two dumps tells you what the thread did in between. Five seconds later, in the second dump, `issuer-refresh` still shows `cpu=11.62ms`: it used nothing. `fee-recalc` went from 3,689.36 ms to 8,882.05 ms while `elapsed` went from 3.96 s to 9.31 s. That's 5.19 seconds of CPU in 5.35 seconds, about 97% of one core.

On Linux, `top -H -p <pid>` shows the same thing per thread, live:

```text
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
29196 root      20   0 7234372 158840  18608 R  99.9   1.0   0:15.31 fee-recalc
29170 root      20   0 7234372 158840  18608 S   0.0   1.0   0:00.14 java
```

The PID column in `top -H` is the Linux thread id. It's the same number as `nid=` and the number in brackets in the dump, so you can search the dump for `nid=29196`. Since JDK 18 the dump prints `nid` in decimal (change JDK-8268425). JDK 17 and older print it in hex, `nid=0x720c`, so convert first with `printf '%x\\n' 29196`. The JVM also gives each OS thread its Java name, cut to 15 characters, so `top` often shows the name straight away.

Inside a container you may not have `top`. Two dumps and `cpu=` work everywhere.

Check: a thread shows the same stack and `cpu=` grows by 4,900 ms between two dumps 5 seconds apart. Is it stuck? (No. It's hot: a loop that never leaves that frame.)"""

S3 = """Four `auth-worker` threads waiting to lock `<0x0000000735c101a0>` are a queue at one door. The question is who's inside. Search the same dump for that address with `- locked`:

```text
"issuer-refresh" #23 [29189] prio=5 os_prio=0 cpu=11.62ms elapsed=4.17s tid=0x00007f6fe41b7430 nid=29189 runnable  [0x00007f6fe8a4a000]
   java.lang.Thread.State: RUNNABLE
\tat sun.nio.ch.SocketDispatcher.read0(java.base@25.0.5.0.3/Native Method)
\t...
\tat java.net.Socket$SocketInputStream.read(java.base@25.0.5.0.3/Socket.java:958)
\tat workbench.performance.l08.FrozenServiceKt.main$lambda$0(FrozenService.kt:26)
\t- locked <0x0000000735c101a0> (a java.lang.Object)
```

The `- locked` line sits under the frame that entered `synchronized`. So `issuer-refresh` took the cache lock in its own code, then called the card issuer, and is waiting for an answer with the lock still held. Every request that needs the cache now waits for the issuer. The fix isn't in the four blocked threads. Make the remote call outside the lock, give the socket a read timeout, and take the lock only to swap in the result.

A `ReentrantLock` shows up differently. The waiter says `- parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)`, but the owner prints no `- locked` line, because a `ReentrantLock` isn't tied to a stack frame. That's what `-l` is for: it ends each thread with the `java.util.concurrent` locks it owns.

```text
"ledger-writer" ...
   java.lang.Thread.State: TIMED_WAITING (sleeping)
\t...
   Locked ownable synchronizers:
\t- <0x0000000735c11100> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
```

Without `-l`, you can see that `ledger-reader` waits, but not for whom. `issuer-refresh` lists one too: the socket's own read lock inside `NioSocketImpl`. A thread can hold several.

Keep following. The owner may itself wait for another lock, and so on. If the chain comes back to a thread you already passed, it's a deadlock (lesson 6 of the threads track), and the JVM prints `Found one Java-level deadlock` at the end of the dump.

Not every parked thread is stuck. An idle pool thread shows `- parking to wait for <0x...> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)` under `LinkedBlockingQueue.take` and `ThreadPoolExecutor.getTask`. A condition has no owner, so the chain ends there. It's a worker waiting for a task, and none of your code is in its stack.

Check: 30 threads are parked inside your connection pool's `getConnection`, and no thread holds a lock they want. What does the dump not show you? (Who holds the 20 connections. Look for the threads whose stacks show they are using a connection, for example inside a JDBC call.)"""

TABLE = """| Same frames in every dump? | CPU grew? | Your code in the stack? | What it is |
|---|---|---|---|
| yes | no | yes | Stuck: waiting for a lock, a socket or a queue. Follow its lock line. |
| yes | yes | yes | Hot: a loop that never leaves that frame |
| no | either | yes | Working: it moves through the code |
| yes | no | no | Idle: a pool or JVM thread waiting for work |"""

S4 = f"""One dump is a photo. A thread caught in a database call might finish 2 ms later. Take three, a few seconds apart, and compare each thread across them:

```bash
for i in 1 2 3; do jcmd $PID Thread.print -l > dump-$i.txt; sleep 5; done
```

{TABLE}

This lesson's lab turns that table into code.

One caution for hot threads. The dump stops threads at safepoints, so a hot thread's top frame is where it reached the next safepoint poll, not always the line that costs the most. That's the safepoint bias from lesson 6. In `fee-recalc` the whole loop is one line, so the dump is right. In a big method, confirm with async-profiler.

Now the virtual threads. The demo also started 10,000 virtual threads that wait for a permit and 200 that sleep. `Thread.print` shows none of them, only the four idle carrier threads `ForkJoinPool-1-worker-1` to `-4`. Virtual threads need the newer dump format from JEP 444:

```bash
jcmd $PID Thread.dump_to_file /tmp/threads.txt                 # plain text, includes virtual threads
jcmd $PID Thread.dump_to_file -format=json /tmp/threads.json   # the same, for tools
```

On JDK 25 each virtual thread looks like this. On JDK 21 the first line has no state, and there are no lock lines:

```text
#34 "vt-auth" virtual WAITING 2026-11-16T05:49:23.834387205Z
    at java.base/java.lang.VirtualThread.park(VirtualThread.java:745)
    - parking to wait for <java.util.concurrent.Semaphore$NonfairSync@73e2d24e>
    at java.base/java.lang.System$1.parkVirtualThread(System.java:2285)
```

Nobody reads 10,200 stacks. Group them by the first frame of your own code and read the biggest group:

```bash
awk 'BEGIN {{ RS = ""; FS = "\\n" }} / virtual / {{ for (i = 2; i <= NF; i++) if ($i ~ /workbench\\./) {{ n[$i]++; break }} }} END {{ for (k in n) print n[k], k }}' /tmp/threads.txt | sort -rn
```

```text
10000     at workbench.performance.l08.FrozenServiceKt.main$lambda$6$0(FrozenService.kt:44)
200     at workbench.performance.l08.FrozenServiceKt.main$lambda$7$0(FrozenService.kt:45)
```

Ten thousand requests wait at line 44, for a permit. That's your incident. The Javadoc of `HotSpotDiagnosticMXBean.dumpThreads`, which this command uses, says the dump includes every platform thread and "may include some or all virtual threads", so read the counts as close, not exact.

Check: you take three plain dumps of a virtual-thread service, and the biggest group grows from 2,000 to 6,000 to 9,000 threads at the same frame. What do you know? (Requests arrive faster than that frame lets them through. Something downstream of it is slow or stuck.)"""

lesson = {
    "id": "perf-08",
    "title": "Reading thread dumps: stuck, blocked and hot threads",
    "minutes": 38,
    "goal": "By the end you can take thread dumps from a running JVM, read each thread's name, state, stack and lock lines, follow a blocked thread to the thread that holds it up, find a hot thread from its CPU time, and compare dumps over time to tell stuck threads from busy and idle ones, including thousands of virtual threads.",
    "warmup": {
        "q": "A dump shows a thread in state `RUNNABLE`, at the top of its stack `sun.nio.ch.SocketDispatcher.read0`. A second dump 5 seconds later shows the same stack and the same `cpu=11.62ms`. What is the thread doing?",
        "options": [
            "Burning a CPU core in a tight loop",
            "Waiting for bytes from the network: the JVM reports a thread in native code as RUNNABLE even while the OS has it asleep",
            "It is deadlocked with another thread",
            "Nothing: the dump is wrong, because a RUNNABLE thread always uses CPU",
        ],
        "answer": 1,
        "why": "The JVM can't see inside native code, so a thread in a native socket read counts as RUNNABLE. Its CPU time didn't move in 5 seconds, so it isn't computing: the kernel has it asleep until data arrives. A hot loop would add about 5,000 ms of CPU, and a deadlock shows BLOCKED or parked threads with lock lines.",
    },
    "sections": [
        {"h": "A thread dump is every stack, printed at one safepoint", "body": S1,
         "try": {"title": "Take your first dump", "minutes": 5,
                 "steps": [
                     "Run the demo. It prints its PID and stays frozen for 120 seconds (pass `-Pargs=300` for longer).",
                     "In a second terminal, run `jcmd` to confirm the PID, then `jcmd <pid> Thread.print -l > dump-1.txt`.",
                     "Predict before you look: which state will the four `auth-worker` threads be in, and at which line of `FrozenService.kt`?",
                     "Open `dump-1.txt`. Find the four `auth-worker` threads, their state line, their first frame in `workbench.performance.l08` and the address they wait for. Then search for `vt-auth`.",
                 ],
                 "code": demo("FrozenService", "FrozenServiceJava"),
                 "expect": "The four `auth-worker` threads are `BLOCKED (on object monitor)` in `authorize` at `FrozenService.kt:54`, and all wait to lock the same address. There's no `main` thread (it returned) and no `vt-auth` at all: `Thread.print` lists only platform threads. Section 4 deals with the virtual ones. In the Java version the line numbers differ, and the frames say `FrozenServiceJava`."},
         "refs": [{"title": "The jcmd command (JDK 25)", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html", "kind": "docs"}]},
        {"h": "RUNNABLE doesn't mean busy: compare cpu= between dumps", "body": S2,
         "try": {"title": "Find the hot thread two ways", "minutes": 4,
                 "steps": [
                     "With the demo still running, take a second dump about 5 seconds after the first: `jcmd <pid> Thread.print -l > dump-2.txt`.",
                     "Predict: which of `issuer-refresh` and `fee-recalc` will show more CPU in the second dump?",
                     "Run the two `grep` lines below and work out how much CPU each thread used between the dumps.",
                     "On Linux, run `top -H -p <pid>` and match the busy thread's PID to a `nid=` in the dump.",
                 ],
                 "code": {"lang": "bash", "title": "terminal 2",
                          "src": "grep -h '^\"fee-recalc\"' dump-1.txt dump-2.txt | grep -o 'cpu=[0-9.]*ms elapsed=[0-9.]*s'\ngrep -h '^\"issuer-refresh\"' dump-1.txt dump-2.txt | grep -o 'cpu=[0-9.]*ms elapsed=[0-9.]*s'\ntop -H -b -n 1 -p <pid> | head -12     # Linux only",
                          "run": ""},
                 "expect": "`fee-recalc` gains about as many milliseconds of CPU as milliseconds passed, so it uses close to one full core. `issuer-refresh` shows the same `cpu=` both times, although it is RUNNABLE. In `top -H`, the top line is `fee-recalc`, and its PID equals its `nid=` in the dump."},
         "refs": [{"title": "ThreadMXBean: per-thread CPU time from inside the JVM", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.management/java/lang/management/ThreadMXBean.html", "kind": "docs"}]},
        {"h": "Follow the lock to the thread that holds everyone up", "body": S3,
         "figure": {"svg": FIG, "caption": "Four BLOCKED workers, one lock, one owner. The owner is RUNNABLE but uses no CPU: it's waiting on a socket with the lock held."},
         "try": {"title": "Find an owner with and without -l", "minutes": 4,
                 "steps": [
                     "Take a dump without `-l`: `jcmd <pid> Thread.print > plain.txt`.",
                     "Find `ledger-reader`, copy the address on its `parking to wait for` line, and search `plain.txt` for that address. Can you find the owner?",
                     "Now search `dump-1.txt` (taken with `-l`) for the same address.",
                     "Run the `awk` line below on `dump-1.txt` with the address the `auth-worker` threads wait for. It prints the name of the thread that holds it.",
                 ],
                 "code": {"lang": "bash", "title": "terminal 2",
                          "src": "jcmd <pid> Thread.print > plain.txt\ngrep -n 'ReentrantLock' plain.txt dump-1.txt\n# who holds a monitor? print the thread whose stack has \"- locked <address>\"\nawk '/^\"/ { name = $1 } /- locked <0x0000000735c101a0>/ { print name }' dump-1.txt",
                          "run": ""},
                 "expect": "In `plain.txt` the address appears only in `ledger-reader`: nothing says who owns it. In `dump-1.txt` it also appears under `ledger-writer`'s `Locked ownable synchronizers`. The `awk` line prints `\"issuer-refresh\"` (use the address from your own dump, it changes every run)."},
         "refs": [{"title": "JEP 444: Virtual Threads (the new thread dump format)", "url": "https://openjdk.org/jeps/444", "kind": "read"}]},
        {"h": "One dump is a photo: take three, and group thousands", "body": S4,
         "try": {"title": "Group the virtual threads", "minutes": 4,
                 "steps": [
                     "With the demo running, write the new dump format: `jcmd <pid> Thread.dump_to_file /tmp/threads.txt` (add `-overwrite` if the file exists).",
                     "Predict: how many groups will the `awk` line print, and which is biggest?",
                     "Run the `awk` line from this section. Then count the virtual threads by state.",
                 ],
                 "code": {"lang": "bash", "title": "terminal 2",
                          "src": "jcmd <pid> Thread.dump_to_file -overwrite /tmp/threads.txt\nawk 'BEGIN { RS = \"\"; FS = \"\\n\" } / virtual / { for (i = 2; i <= NF; i++) if ($i ~ /workbench\\./) { n[$i]++; break } } END { for (k in n) print n[k], k }' /tmp/threads.txt | sort -rn\n# JDK 25: count virtual threads by state\ngrep ' virtual ' /tmp/threads.txt | awk '{print $4}' | sort | uniq -c",
                          "run": ""},
                 "expect": "Two groups: about 10,000 threads at `FrozenService.kt:44` (waiting for a permit) and 200 at line 45 (asleep). On JDK 25 the state count says `10000 WAITING` and `200 TIMED_WAITING`. On JDK 21 the plain format has no state field, so the second count doesn't work."},
         "refs": [{"title": "HotSpotDiagnosticMXBean.dumpThreads (JDK 25)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.management/com/sun/management/HotSpotDiagnosticMXBean.html", "kind": "docs"}]},
    ],
    "analogy": "A thread dump is a photo of a restaurant kitchen during a rush, taken from the doorway. In one photo you see a cook standing at the stove, four waiters lined up at the pass, and a dishwasher leaning on the wall. You can't tell from one photo whether the cook is cooking or stuck waiting for a delivery. Take three photos ten seconds apart: if the waiters are still in line, the cook is still at the stove and nothing on the stove has changed, the cook is waiting for something, and the waiters are waiting for the cook. The dishwasher leaning on the wall in every photo is just idle. The analogy breaks in two places. Taking the photo freezes everyone for a moment, which a real photo doesn't. And a cook who stands still is visibly idle, while a thread blocked in a socket read reports itself as RUNNABLE, so you need the CPU numbers to see it.",
    "in_your_world": "Your authorization service on Quarkus stops answering, the load balancer marks pods unhealthy, and the obvious move is a rollout restart. Take the evidence first: `kubectl exec <pod> -- jcmd 1 Thread.print -l > dump-1.txt`, three times, 5 seconds apart (in many containers the JVM is PID 1). The usual finds in payments services look like this lesson's demo: request threads BLOCKED behind one thread that holds a lock while it calls a slow issuer or fraud API; worker threads parked inside a connection pool, waiting for a connection that a stuck call holds; or a Kafka consumer thread stuck in the same frame in all three dumps. That last one goes beyond a slow consumer: if it doesn't call `poll` again within `max.poll.interval.ms`, the consumer leaves the group and its partitions get rebalanced. On virtual threads, write `Thread.dump_to_file` and group by your first frame. The biggest group is usually the one slow dependency.",
    "mistake": "The most common mistake is reading one dump and chasing the RUNNABLE threads. People assume RUNNABLE means busy, see 40 RUNNABLE threads, and conclude the service is CPU-bound. Most of them are in native socket reads or `epoll` waits, asleep in the kernel. The fix is a routine: take three dumps 5 seconds apart, compare `cpu=` to find what really burns CPU, and for everything else read the lock lines. Follow each `waiting to lock` or `parking to wait for` to the owner, and fix the owner. The threads in the queue are only the symptom.",
    "compare": {
        "title": "The cpu= column from inside the process, with ThreadMXBean",
        "java": {"title": "HotThreadsJava.java", "src": read(f"{lab}/demo/{J}/HotThreadsJava.java")},
        "kotlin": {"title": "HotThreads.kt", "src": read(f"{lab}/demo/{K}/HotThreads.kt")},
        "note": "Both read the same JVM counters that a dump prints as `cpu=`: sample every thread's CPU time, wait, sample again, and sort by the difference. That's a cheap health endpoint that answers \"which thread is hot\" without `top`. The behavior is identical. Kotlin's `associateWith` and `mapNotNull` replace the two loops, and `LongArray` has no `mapNotNull`, so the Kotlin version calls `toList()` first. One limit applies to both, checked on JDK 21 and 25: `getAllThreadIds()` lists only platform threads, and `getThreadCpuTime` returns -1 for a virtual thread. For virtual threads, use the carrier threads' CPU or a profiler.",
    },
    "worked": {
        "title": "Three dumps of a frozen service, read in five minutes",
        "steps": [
            {"say": "1. Capture the evidence before anyone restarts anything: three dumps, 5 seconds apart, each in its own file.",
             "code": "PID=$(pgrep -f FrozenService | head -1)\nfor i in 1 2 3; do jcmd $PID Thread.print -l > dump-$i.txt; sleep 5; done", "lang": "bash"},
            {"say": "2. Count states to see the shape. Four BLOCKED threads in a service that should never block on a monitor is the first lead. The 12 RUNNABLE ones include JVM threads and threads in native calls, so they prove nothing yet.",
             "code": "grep -h 'java.lang.Thread.State' dump-1.txt | sort | uniq -c | sort -rn\n#   12    java.lang.Thread.State: RUNNABLE\n#    6    java.lang.Thread.State: WAITING (parking)\n#    4    java.lang.Thread.State: BLOCKED (on object monitor)\n#    3    java.lang.Thread.State: TIMED_WAITING (parking)\n#    ...", "lang": "bash"},
            {"say": "3. Ask what the BLOCKED threads want. One address four times means one door, one queue.",
             "code": "grep -h 'waiting to lock' dump-1.txt | sort | uniq -c\n#    4 \t- waiting to lock <0x0000000735c101a0> (a java.lang.Object)", "lang": "bash"},
            {"say": "4. Find who holds it, then check whether the owner is working or waiting. Its stack ends in a socket read, and its CPU time is the same in all three dumps: it's waiting on the network with the lock held.",
             "code": "awk '/^\"/ { name = $1 } /- locked <0x0000000735c101a0>/ { print name }' dump-1.txt\n# \"issuer-refresh\"\ngrep -h '^\"issuer-refresh\"' dump-*.txt | grep -o 'cpu=[0-9.]*ms'\n# cpu=11.62ms\n# cpu=11.62ms\n# cpu=11.62ms", "lang": "bash"},
            {"say": "5. Fix the owner, not the queue. Make the slow call with a deadline and no lock held, then take the lock only to swap in the result. Now a slow issuer delays one refresh, not every request.",
             "code": "IssuerData fresh = issuerClient.fetch(Duration.ofSeconds(2));   // 1. slow call: no lock held, with a deadline\nsynchronized (issuerCache) {                                     // 2. lock only to swap the data\n    issuerCache.replace(fresh);\n}",
             "lang": "java",
             "alt_code": "val fresh = issuerClient.fetch(Duration.ofSeconds(2))   // 1. slow call: no lock held, with a deadline\nsynchronized(issuerCache) {                              // 2. lock only to swap the data\n    issuerCache.replace(fresh)\n}",
             "alt_lang": "kotlin"},
        ],
    },
    "lab": {
        "title": "Read dumps in code: hot, blocked and stuck threads",
        "minutes": 15,
        "files": [f"{lab}/main/{K}/DumpReader.kt"],
        "run": "./gradlew :performance:test --tests 'workbench.performance.l08.*'",
        "steps": [
            "Read `ThreadDump.kt`. The parser is done: it turns each thread of a real `Thread.print -l` dump into a `DumpedThread` with its name, `nid`, state, `cpuMs`, frames, the locks it holds and the lock it waits for.",
            "Open `src/test/resources/workbench/performance/l08/dump-1.txt`. It's a real dump of `FrozenService` on JDK 25, and `dump-2.txt` and `dump-3.txt` were taken 5 and 10 seconds later. The two `deadlock` files come from a small program with two deadlocked refunds and two threads that are both called `worker`.",
            "Write `hottest`: pair each thread in `after` with the same thread in `before` by `nid`, keep the ones whose CPU grew, biggest first, at most `n`. Run the tests: the three `hottest` tests should pass.",
            "Write `blockedChain`: from the named thread, follow `waitsFor` to `ownerOf`, again and again, until a thread waits for nothing or a name comes back.",
            "Write `stuck`: the threads that have the same frames in every dump, your code in the stack, and CPU growth under the budget. Run all the tests.",
        ],
        "hints": [
            "`before.byNid(now.nid)` finds a thread's earlier self. A thread that started between the two dumps has none: skip it.",
            "In `blockedChain`, `thread.waitsFor?.let(dump::ownerOf)` is the next thread in the chain, or null when the chain ends. An idle pool thread waits for a condition object, and nobody owns a condition.",
            "For the cycle, check whether the owner's name is already in your list before you add it. Add it either way, then stop if it was there.",
            "For `stuck`, start from the first dump's threads and look each one up in the others with `byNid`. `==` on two `List<String>` compares every frame. The CPU check needs only the first and the last dump.",
        ],
        "done_when": "All 11 tests in `DumpReaderTest` pass.",
    },
    "drill": {
        "title": "Group a virtual-thread dump from memory",
        "minutes": 5,
        "prompt": "Close this page. Write `groupByFirstAppFrame(dump: String, appPrefix: String)`. It takes the text written by `jcmd <pid> Thread.dump_to_file` and returns, biggest first, how many virtual threads have each first frame of your code. A blank line separates threads, and a virtual thread's first line contains ` virtual`. Each frame line starts with `at ` after its indentation.",
        "answer": {
            "lang": "kotlin",
            "src": "fun groupByFirstAppFrame(dump: String, appPrefix: String): List<Pair<String, Int>> =\n    dump.split(Regex(\"\\\\n\\\\s*\\\\n\"))                                          // 1. one record per thread\n        .map { it.trim() }\n        .filter { record -> \" virtual\" in record.lineSequence().first() }    // 2. only virtual threads\n        .mapNotNull { record ->                                              // 3. its first frame of your code\n            record.lines().map { it.trim() }.firstOrNull { it.startsWith(\"at $appPrefix\") }\n        }\n        .groupingBy { it }.eachCount()                                       // 4. count per frame\n        .toList()\n        .sortedByDescending { it.second }",
            "alt": {
                "lang": "java",
                "src": "static List<Map.Entry<String, Long>> groupByFirstAppFrame(String dump, String appPrefix) {\n    return Arrays.stream(dump.split(\"\\\\n\\\\s*\\\\n\"))                                  // 1. one record per thread\n            .map(String::trim)\n            .filter(r -> r.lines().findFirst().orElse(\"\").contains(\" virtual\"))     // 2. only virtual threads\n            .flatMap(r -> r.lines().map(String::trim)                               // 3. its first frame of your code\n                    .filter(l -> l.startsWith(\"at \" + appPrefix)).limit(1))\n            .collect(Collectors.groupingBy(f -> f, Collectors.counting()))         // 4. count per frame\n            .entrySet().stream()\n            .sorted(Map.Entry.<String, Long>comparingByValue().reversed())\n            .toList();\n}",
            },
        },
    },
    "recap": [
        "`jcmd <pid> Thread.print -l` prints every platform thread's state, stack and locks at one safepoint. Take it before you restart, and use `kill -3` if `jcmd` can't attach.",
        "Read each thread by name, state, the first frame of your code, then the lock lines: `locked`, `waiting to lock`, `parking to wait for`, `waiting on`.",
        "RUNNABLE only means \"not waiting for a Java lock\". Compare `cpu=` between two dumps, or use `top -H`, whose PID is the dump's `nid` (decimal since JDK 18).",
        "For a blocked thread, follow the lock to its owner and fix the owner. For `java.util.concurrent` locks you need `-l` to see who owns them.",
        "Take three dumps a few seconds apart: same frames and flat CPU means stuck, same frames and rising CPU means hot, no frames of yours means idle.",
        "Virtual threads only appear in `Thread.dump_to_file`. Group them by your first frame and read the biggest group.",
    ],
    "quiz": [
        {"q": "A dump shows 30 threads `WAITING (parking)` with `- parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)`, all the same address. No thread's stack shows `- locked` with that address. What do you do next?",
         "options": [
             "Conclude the lock is free and the dump caught a hand-off",
             "Take the dump again with `-l` and look for the address under some thread's `Locked ownable synchronizers`",
             "Restart the service, since parked threads can't be diagnosed",
             "Look for `Found one Java-level deadlock`, because parked threads always mean a deadlock",
         ],
         "answer": 1,
         "why": "A `ReentrantLock` isn't tied to a stack frame, so its owner never prints `- locked`. With `-l`, each thread lists the `java.util.concurrent` locks it owns, and that's where the owner shows up. A free lock wouldn't keep 30 threads parked, and parked threads are often just queued behind a slow owner, not deadlocked."},
        {"q": "`top -H -p 4100` on a JDK 25 service shows thread PID 4187 at 100% CPU. How do you find it in the dump?",
         "options": [
             "Search for `nid=4187` or `[4187]` in the header lines",
             "Convert 4187 to hex and search for `nid=0x105b`",
             "Search for `#4187`, the Java thread number",
             "You can't: top's thread ids aren't in thread dumps",
         ],
         "answer": 0,
         "why": "The `top -H` PID is the Linux thread id, which the dump prints as `nid=` and in brackets. Since JDK 18 it's printed in decimal, so search for it as is. Hex conversion was needed on JDK 17 and older. `#N` is the Java thread id, a different number."},
        {"q": "Three dumps 5 seconds apart. Thread `settle-worker-2` is in `LinkedBlockingQueue.take` under `ThreadPoolExecutor.getTask` in all three, with the same CPU time, and no frame from your code. What is it?",
         "options": [
             "Stuck: same frames and flat CPU in every dump",
             "Hot: it never leaves that frame",
             "Idle: a pool worker waiting for a task, which is normal",
             "Deadlocked with the thread that should put work on the queue",
         ],
         "answer": 2,
         "why": "Same frames and flat CPU fit both stuck and idle. What decides it is whose code is waiting. With no frame of yours, it's the pool's own loop waiting for the next task. It parks on a condition object, which has no owner, so there's nobody to follow. Stuck threads have your code in the stack, waiting on something your code asked for."},
        {"q": "Your service runs 8,000 requests on virtual threads. `jcmd <pid> Thread.print` shows about 40 threads and none of your request code. Why?",
         "options": [
             "The requests already finished",
             "`Thread.print` lists platform threads only. Use `jcmd <pid> Thread.dump_to_file`, which includes virtual threads",
             "Virtual threads have no stacks until they are mounted",
             "You need `-l` to see virtual threads",
         ],
         "answer": 1,
         "why": "The classic dump lists platform threads, so you see the carrier threads but not the virtual threads on them. JEP 444 added `Thread.dump_to_file` (plain or JSON), which includes virtual threads, mounted or not. `-l` only adds lock ownership to the classic dump."},
        {"q": "A hot thread's dump shows its top frame at the end of a short loop in `computeFee`, but async-profiler puts most of its CPU in `BigDecimal.divide`, which `computeFee` calls inside that loop. Which is right, and why?",
         "options": [
             "The dump: it's taken from the real thread, so its top frame is exact",
             "Neither: both tools sample at random",
             "async-profiler: a thread dump stops threads at safepoint polls, such as loop back-edges, so it reports where the thread reached the next poll",
             "The dump, because async-profiler can't see inlined methods",
         ],
         "answer": 2,
         "why": "A thread dump is taken at a safepoint, so it has the safepoint bias from lesson 6: a hot thread is caught at its next poll, often a loop back-edge or a method return, not at the instruction that costs the most. async-profiler interrupts the thread wherever it is, and it does show inlined frames. Use dumps to find which thread is hot, and a profiler to find where its time goes.",
         "from": "perf-06"},
    ],
    "flashcards": [
        {"front": "A thread is RUNNABLE in `SocketDispatcher.read0` and its `cpu=` doesn't change between dumps. What is it doing?", "back": "Waiting for network bytes. The JVM reports threads in native code as RUNNABLE; the OS has it asleep."},
        {"front": "How do you tell a hot thread from a stuck one, with only thread dumps?", "back": "Take two dumps a few seconds apart and compare `cpu=`. Same frames and rising CPU is hot; same frames and flat CPU is stuck."},
        {"front": "`top -H` shows thread 29196 busy. Where is it in a JDK 18+ dump?", "back": "Search for `nid=29196`. Since JDK 18 the nid is decimal; JDK 17 and older print hex."},
        {"front": "Which `jcmd` option shows who owns a `ReentrantLock`?", "back": "`Thread.print -l`. It lists each thread's `Locked ownable synchronizers`. Without it, only the waiters show."},
        {"front": "What does `- waiting on <a>` mean, compared with `- waiting to lock <a>`?", "back": "`waiting on`: inside `Object.wait()`, the monitor is given back. `waiting to lock`: BLOCKED, trying to enter `synchronized` on `a`."},
        {"front": "Your virtual threads don't appear in `jcmd <pid> Thread.print`. What do you run instead?", "back": "`jcmd <pid> Thread.dump_to_file <file>` (add `-format=json` for tools). Then group threads by their first frame."},
        {"front": "Why can't you match a lock address like `<0x0000000735c101a0>` across two dumps?", "back": "It's the object's heap address at that moment, and a GC can move the object between dumps. It's reliable only within one dump."},
    ],
    "terms": [
        {"term": "thread dump", "plain": "A printout of every thread's name, state, stack and locks at one moment."},
        {"term": "safepoint", "plain": "A point where the JVM knows the full state of every frame, so it can stop a thread there and read its stack."},
        {"term": "nid", "plain": "The OS thread id in a dump header. It's the PID column of `top -H`."},
        {"term": "monitor", "plain": "The lock that `synchronized` takes on an object. A dump shows it as `- locked <address>`."},
        {"term": "ownable synchronizer", "plain": "A `java.util.concurrent` lock, such as `ReentrantLock`, that a thread owns. `Thread.print -l` lists them per thread."},
        {"term": "carrier thread", "plain": "A platform thread that runs virtual threads. A classic dump shows the carriers but not the virtual threads."},
    ],
    "explain_back": {
        "prompt": "Explain to a teammate how you'd find out why a service has stopped answering, using only thread dumps. Say what you'd capture, what you'd compare, and how you'd decide which thread to fix.",
        "answer": "Before anyone restarts it, I'd take three dumps with `jcmd <pid> Thread.print -l`, 5 seconds apart. In each thread I read the name, the state, the first frame of our code and the lock lines. I don't trust RUNNABLE, because threads in native socket reads are RUNNABLE too, so I compare `cpu=` between dumps. A thread whose CPU rises in the same frame is hot. For blocked or parked threads I follow the lock: the address on `waiting to lock` or `parking to wait for` leads to the thread that holds it, under `- locked` or, for `ReentrantLock`, under `Locked ownable synchronizers`. I keep following until I reach a thread that is waiting for something outside the JVM, like a socket, or until the chain loops, which is a deadlock. That owner is what I fix. Threads with the same frames, flat CPU and none of our code are just idle pool threads. On virtual threads I'd use `Thread.dump_to_file` and group the threads by their first frame, then read the biggest group.",
    },
    "deeper": {
        "minutes": 10,
        "body": """The JSON format is what you'd feed a tool. On JDK 25 each thread has `tid`, `name`, `state`, `stack`, and lock fields: `parkBlocker` with the parked-on object and its `owner` thread id, `blockedOn` for a monitor a thread wants, `waitingOn`, and `monitorsOwned`. On JDK 21 a thread has only `tid`, `name` and `stack`. The JSON also groups threads by **thread container**: `<root>`, each thread pool, and each executor made by `Executors.newVirtualThreadPerTaskExecutor()`. In this lesson's demo, `<root>` holds 10,212 threads, because the demo starts its virtual threads with `Thread.ofVirtual()` directly, and each `ThreadPoolExecutor` holds its own workers. With virtual threads, that grouping often says more than the stacks do.

```bash
jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json
jq '.threadDump.threadContainers[] | {container, threadCount}' /tmp/threads.json
```

`Thread.print -e` adds `allocated=` and `defined_classes=` to each header. That's another cheap way to find the thread that allocates the most, besides JFR.

If the JVM is so stuck that it can't reach a safepoint, `jcmd` and `kill -3` both hang, because both need one. The last resort is `jhsdb jstack --pid <pid>`. It reads the process from outside, like a debugger, so it needs permission to attach to the process (ptrace on Linux) and pauses the whole JVM while it reads. Use it only when the normal dump won't come.

In code, `ThreadMXBean.dumpAllThreads(true, true)` returns the same information as `Thread.print -l` as `ThreadInfo` objects, and `findDeadlockedThreads()` runs the deadlock check. Both cover platform threads only. A health check that runs `findDeadlockedThreads()` every minute costs a safepoint each time. It's small, but measure it before you add it to a latency-sensitive service.""",
    },
    "sources": [
        {"title": "The jcmd command, JDK 25", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html"},
        {"title": "JEP 444: Virtual Threads (thread dumps section)", "url": "https://openjdk.org/jeps/444"},
        {"title": "HotSpotDiagnosticMXBean.dumpThreads, JDK 25", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.management/com/sun/management/HotSpotDiagnosticMXBean.html"},
        {"title": "ThreadMXBean, JDK 25", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.management/java/lang/management/ThreadMXBean.html"},
        {"title": "JDK-8268425: Show decimal nid of OSThread instead of hex format one (the commit)", "url": "https://github.com/openjdk/jdk/commit/a9e201016de119af4b0fd3ebb43768896fb9e5c5"},
    ],
}

out = ROOT / "content/lessons/perf-08.json"
out.write_text(json.dumps(lesson, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
