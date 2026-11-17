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
            f'<text class="t" x="100" y="{y + 20}" text-anchor="middle">report-worker-{i}</text>'
            f'<text class="t-s t-bad" x="100" y="{y + 37}" text-anchor="middle">BLOCKED</text>'
            f'<line class="ln-bad" x1="180" y1="{y + 23}" x2="278" y2="135" marker-end="url(#arr)"/>\n')


FIG = ('<svg viewBox="0 0 680 270" role="img" aria-label="Four report-worker threads are BLOCKED waiting to lock the '
       'catalog lock. The lock is held by catalog-refresh, which is RUNNABLE with flat CPU, inside a socket read to a '
       'document store that never answers.">\n'
       '<text class="t-s t-bad" x="230" y="14" text-anchor="middle">waiting to lock</text>\n'
       + worker(1, 20) + worker(2, 78) + worker(3, 136) + worker(4, 194)
       + '<rect class="box-b" x="280" y="105" width="140" height="60" rx="8"/>'
         '<text class="t" x="350" y="130" text-anchor="middle">catalog lock</text>'
         '<text class="t-s t-code" x="350" y="150" text-anchor="middle">0x…35c08070</text>\n'
         '<line class="ln" x1="420" y1="135" x2="488" y2="135" marker-end="url(#arr)"/>'
         '<text class="t-s" x="455" y="126" text-anchor="middle">held by</text>\n'
         '<rect class="box-a" x="490" y="95" width="180" height="80" rx="8"/>'
         '<text class="t" x="580" y="120" text-anchor="middle">catalog-refresh</text>'
         '<text class="t-s t-m" x="580" y="140" text-anchor="middle">RUNNABLE, cpu flat</text>'
         '<text class="t-s t-code" x="580" y="160" text-anchor="middle">SocketDispatcher.read0</text>\n'
         '<line class="ln-d" x1="580" y1="175" x2="580" y2="213" marker-end="url(#arr)"/>'
         '<text class="t-s t-m" x="588" y="198" text-anchor="start">socket read</text>\n'
         '<rect class="box-dim" x="490" y="215" width="180" height="44" rx="8"/>'
         '<text class="t" x="580" y="242" text-anchor="middle">store: no answer</text>\n'
         '</svg>')

HEADER = """\
"report-worker-3" #24 [25043] prio=5 os_prio=0 cpu=0.36ms elapsed=11.19s tid=0x00007ff4242e2bc0 nid=25043 waiting for monitor entry  [0x00007ff40888d000]
   java.lang.Thread.State: BLOCKED (on object monitor)
\tat workbench.performance.l08.FrozenServiceKt.writeReport(FrozenService.kt:54)
\t- waiting to lock <0x0000000735c08070> (a java.lang.Object)
\tat workbench.performance.l08.FrozenServiceKt.main$lambda$1$0(FrozenService.kt:32)
\tat workbench.performance.l08.FrozenServiceKt$$Lambda/0x000000001e083000.run(Unknown Source)
\tat java.util.concurrent.ThreadPoolExecutor.runWorker(java.base@25.0.5.0.3/ThreadPoolExecutor.java:1090)
\tat java.util.concurrent.ThreadPoolExecutor$Worker.run(java.base@25.0.5.0.3/ThreadPoolExecutor.java:614)
\tat java.lang.Thread.runWith(java.base@25.0.5.0.3/Thread.java:1487)
\tat java.lang.Thread.run(java.base@25.0.5.0.3/Thread.java:1474)"""

OPENING = """Picture the restaurant at the worst moment of a night: nothing is leaving the kitchen. You can't stop the evening to question every cook, but you can take a photo through the door. In it, four waiters queue at the counter for the one order book. A cook stands at the back door with that book under his arm, waiting for a delivery. Another cook stirs a pot so hard it splashes. One photo can't say who is stuck and who is busy. Three photos, ten seconds apart, can.

A thread dump is that photo of a JVM: every thread, what it's doing, and which lock it holds or wants. The trap is to read one dump and trust the word RUNNABLE. In this lesson's demo, the thread holding everyone up is RUNNABLE and uses no CPU at all.

Lesson 7's loop barely sees threads that wait. In this lesson, we'll take dumps of a frozen report service, read one thread line by line, tell a waiting thread from a busy one, follow a lock to its owner and compare dumps over time. Before we start, make a guess, and keep it in mind."""

S1 = f"""Meet the patient. `FrozenService` is the report service on a bad day, stuck in five ways at once. A thread refreshes the catalog, the service's list of every document and the shelf it's on, while holding the catalog's lock. It asks the document store for the new list, and the store never answers. Four report workers need the same lock. There's also an idle pool, a busy loop, a second kind of lock, and 10,200 virtual threads. Run it, and it waits for you to look.

A **thread dump** is a printout of every thread in the JVM at one moment: its name, its state, its stack, and the locks it holds or wants. `jcmd <pid> Thread.print` asks the JVM for one. `jcmd` is the JDK tool that sends commands to a running JVM, and `<pid>` is the process id the operating system gave it. The JVM stops every Java thread at a **safepoint**, a point where it knows the full state of each frame (lesson 6 showed why profilers need one). While the threads stand still, it walks each stack and prints it, and then they all run on.

That pause is the photo's flash. With `-Xlog:safepoint` on JDK 25, the safepoint called `PrintThreads` took 36 to 74 ms for 28 threads on this busy 4-core machine. That's fine a few times on a live service. `jstack <pid>` prints the same dump.

```bash
jcmd                                    # lists Java processes and their PIDs
jcmd <pid> Thread.print -l > dump-1.txt # every platform thread, plus the java.util.concurrent locks each one owns
```

Take the dump before anyone restarts a frozen service, because a restart throws the evidence away. If `jcmd` can't attach (it must run as the same operating-system user as the JVM), `kill -3 <pid>` sends the signal SIGQUIT, and the JVM prints the same dump to its own standard output.

Here's one thread from a real dump of the demo on JDK 25:

```text
{HEADER}
```

Read each thread in this order.

1. The name. `report-worker-3` says which pool and which job, which is why the executors track had you name your threads. Unnamed threads all look like `pool-3-thread-7`.
2. The state line. `BLOCKED (on object monitor)` means it wants to enter a `synchronized` block that another thread is inside. A monitor is the lock behind `synchronized`.
3. The frames, top first, down to the first line of your own code: `FrozenService.kt:54`. That's where it is now. The frames below say how it got there.
4. The lock lines, which start with `-`. `- locked <a>` means it holds the monitor of object `a`. `- waiting to lock <a>` means it wants it. `- parking to wait for <a>` means a `java.util.concurrent` lock, condition or queue has parked it, put it to sleep until someone wakes it. `- waiting on <a>` means it's inside `Object.wait()` and has given `a` back.

The number in `<0x0000000735c08070>` is the object's address in the heap at that moment. Inside one dump, the same address means the same object. Between dumps, a garbage collection may have moved the object, so don't match addresses across dumps.

**Take the dump before you restart. Read each thread by name, state, first frame of your code, then its lock lines.**

Check yourself: in one dump, four threads show `- waiting to lock` with the same address, and no thread shows `- locked` with it. What does that mean? (A thread holding it would show `- locked`. If none does, the lock was released a moment ago, and the next dump will tell.)

The demo's busiest-looking threads say RUNNABLE. That word deserves a closer look."""

S2 = """Both of these threads are `RUNNABLE`. One is burning a CPU core, and the other is asleep:

```text
"catalog-refresh" #21 [25040] prio=5 os_prio=0 cpu=25.09ms elapsed=11.41s tid=0x00007ff4242d8600 nid=25040 runnable  [0x00007ff408b8d000]
   java.lang.Thread.State: RUNNABLE
\tat sun.nio.ch.SocketDispatcher.read0(java.base@25.0.5.0.3/Native Method)

"index-rebuild" #28 [25047] prio=5 os_prio=0 cpu=4089.43ms elapsed=11.18s tid=0x00007ff4242e7ac0 nid=25047 runnable  [0x00007ff40848c000]
   java.lang.Thread.State: RUNNABLE
\tat workbench.performance.l08.FrozenServiceKt.rebuildIndex(FrozenService.kt:61)
```

The state is what the JVM knows, and the JVM can't see inside native code, code that runs outside Java in the operating system. When a thread calls a native method like `read0`, the JVM marks it "in native" and reports `RUNNABLE`, because that native code could be computing. Here the kernel, the core of the operating system, has the thread asleep until bytes arrive from the network. That's the cook at the back door: standing at his post, doing nothing. **RUNNABLE means "not waiting for a Java lock", not "using the CPU".**

The `cpu=` field tells them apart. It's the CPU time the operating system has charged to that thread since it started, the cook's step counter. One value means little. The change between two dumps says what the thread did in between. In the second dump, 5.6 seconds later, `catalog-refresh` still shows `cpu=25.09ms`: it used nothing. `index-rebuild` went from 4,089.43 ms to 6,288.02 ms while `elapsed` went from 11.18 s to 16.82 s. That's 2.2 seconds of CPU in 5.6 seconds, about 39% of one core. On a quiet machine it would be close to 100%. This one was shared with more than 30 busy programs.

On Linux, `top -H -p <pid>` shows the same thing per thread, live:

```text
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU  %MEM     TIME+ COMMAND
25047 root      20   0 7219012 186784  23404 R  80.0   1.1   0:12.57 index-rebuild
25014 root      20   0 7219012 186784  23404 S   0.0   1.1   0:00.00 java
```

The PID column of `top -H` is the Linux thread id. It's the same number as `nid=` and the number in brackets in the dump, so you can search the dump for `nid=25047`. Since JDK 18 the dump prints `nid` in decimal (change JDK-8268425). JDK 17 and older print it in hex, `nid=0x61d7`, so convert first with `printf '%x\\n' 25047`. The JVM also gives each operating-system thread its Java name, cut to 15 characters, so `top` often shows the name straight away.

Inside a container you may not have `top`. Two dumps and `cpu=` work everywhere.

Check yourself: a thread shows the same stack in two dumps 5 seconds apart, and its `cpu=` grew by 4,900 ms. Is it stuck? (No. It's hot: a loop that never leaves that frame.)

`catalog-refresh` isn't stuck in the usual sense, then. It's waiting, and it's holding something while it waits."""

S3 = """Four `report-worker` threads waiting to lock `<0x0000000735c08070>` are a queue at one door. The question is who's inside. Search the same dump for that address with `- locked`:

```text
"catalog-refresh" #21 [25040] prio=5 os_prio=0 cpu=25.09ms elapsed=11.41s tid=0x00007ff4242d8600 nid=25040 runnable  [0x00007ff408b8d000]
   java.lang.Thread.State: RUNNABLE
\tat sun.nio.ch.SocketDispatcher.read0(java.base@25.0.5.0.3/Native Method)
\t...
\tat java.net.Socket$SocketInputStream.read(java.base@25.0.5.0.3/Socket.java:958)
\tat workbench.performance.l08.FrozenServiceKt.main$lambda$0(FrozenService.kt:26)
\t- locked <0x0000000735c08070> (a java.lang.Object)
```

The `- locked` line sits under the frame that entered `synchronized`. So `catalog-refresh` took the catalog lock in its own code, then called the document store, and is waiting for an answer with the lock still held. Every report that needs the catalog now waits for the store. That's the cook at the back door with the order book under his arm. The fix isn't in the four blocked threads. Make the slow call outside the lock, give the socket a read timeout, and take the lock only to swap in the result.

A `ReentrantLock`, the JDK's other kind of lock, shows up differently. The waiter says `- parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)`, but its owner prints no `- locked` line, because a `ReentrantLock` isn't tied to a stack frame. That's what `-l` is for: it ends each thread with the `java.util.concurrent` locks it owns.

```text
"archive-writer" #29 [25048] prio=5 os_prio=0 cpu=0.19ms elapsed=11.18s ... waiting on condition
   java.lang.Thread.State: TIMED_WAITING (sleeping)
\t...
   Locked ownable synchronizers:
\t- <0x0000000735c10a88> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)
```

Without `-l`, you can see that `archive-reader` waits, but not for whom. `catalog-refresh` lists one too: the socket's own read lock inside `NioSocketImpl`. A thread can hold several locks.

Keep following. The owner may itself wait for another lock, and so on. If the chain comes back to a thread you already passed, it's a deadlock, two cooks each holding the pan the other needs. The JVM checks for that while it prints, and adds `Found one Java-level deadlock` at the end of the dump, with both threads.

Not every parked thread is stuck. An idle pool thread, such as `export-worker-1`, shows `- parking to wait for <0x...> (a java.util.concurrent.locks.AbstractQueuedSynchronizer$ConditionObject)` under `LinkedBlockingQueue.take` and `ThreadPoolExecutor.getTask`. A condition has no owner, so the chain ends there. It's a worker waiting for a task, leaning on the wall, and none of your code is in its stack.

**Follow every wait to its owner, and fix the owner. The queue is only the symptom.**

Check yourself: 30 threads are parked inside your connection pool's `getConnection`, and no thread holds a lock they want. What doesn't the dump show you? (Who holds the 20 connections. Look for the threads whose stacks show they're using one, for example inside a database call.)

A photo shows where everyone stands. It can't show who's moving."""

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

One caution about hot threads. The dump stops threads at safepoints, so a hot thread's top frame is where it reached the next safepoint poll, not always the line that costs the most. That's the safepoint bias from lesson 6. In `index-rebuild` the whole loop is one line, so the dump is right. In a big method, confirm with async-profiler.

Now the virtual threads, the JDK's lightweight threads that run on a few ordinary ones. The demo started 10,000 virtual threads that wait for a permit and 200 that sleep. `Thread.print` shows none of them, only the four idle carrier threads, `ForkJoinPool-1-worker-1` to `-4`, that would run them. In the kitchen, the photo shows the cooks and not the order tickets pinned on the rail. Virtual threads need the newer dump format that came with them (JEP 444):

```bash
jcmd $PID Thread.dump_to_file /tmp/threads.txt                 # plain text, includes virtual threads
jcmd $PID Thread.dump_to_file -format=json /tmp/threads.json   # the same, for tools
```

On JDK 25 each virtual thread looks like this. On JDK 21 the first line has no state, and there are no lock lines:

```text
#32 "vt-report" virtual WAITING 2026-11-17T08:09:26.520624548Z
    at java.base/java.lang.VirtualThread.park(VirtualThread.java:745)
    - parking to wait for <java.util.concurrent.Semaphore$NonfairSync@4deadc8d>
    at java.base/java.lang.System$1.parkVirtualThread(System.java:2285)
```

Nobody reads 10,200 stacks. Group them by the first frame of your own code, and read the biggest group:

```bash
awk 'BEGIN {{ RS = ""; FS = "\\n" }} / virtual / {{ for (i = 2; i <= NF; i++) if ($i ~ /workbench\\./) {{ n[$i]++; break }} }} END {{ for (k in n) print n[k], k }}' /tmp/threads.txt | sort -rn
```

```text
10000     at workbench.performance.l08.FrozenServiceKt.main$lambda$6$0(FrozenService.kt:44)
200     at workbench.performance.l08.FrozenServiceKt.main$lambda$7$0(FrozenService.kt:45)
```

Ten thousand reports wait at line 44, for a permit. That's your incident. The Javadoc of `HotSpotDiagnosticMXBean.dumpThreads`, which this command uses, says the dump includes every platform thread and "may include some or all virtual threads", so read the counts as close, not exact.

Check yourself: you take three dumps of a service on virtual threads, and the biggest group grows from 2,000 to 6,000 to 9,000 threads at the same frame. What do you know? (Requests arrive faster than that frame lets them through. Something downstream of it is slow or stuck.)

Here's the limit of a dump. It shows who waits, and for whom. It can't say why the document store doesn't answer, how long each call took, or what happened a minute ago. For that, go back to the recordings of lesson 5, and to the store's own evidence."""

lesson = {
    "id": "perf-08",
    "title": "Reading thread dumps: stuck, blocked and hot threads",
    "minutes": 38,
    "goal": "By the end you can take thread dumps from a running JVM, read each thread's name, state, stack and lock lines, follow a blocked thread to the thread that holds it up, find a hot thread from its CPU time, and compare dumps over time to tell stuck threads from busy and idle ones, including thousands of virtual threads.",
    "opening": OPENING,
    "warmup": {
        "q": "A dump shows a thread in state `RUNNABLE`, with `sun.nio.ch.SocketDispatcher.read0` at the top of its stack. A second dump, 5 seconds later, shows the same stack and the same `cpu=25.09ms`. What is the thread doing?",
        "options": [
            "Burning a CPU core in a tight loop",
            "Waiting for bytes from the network: the JVM reports a thread in native code as RUNNABLE even while the operating system has it asleep",
            "It's deadlocked with another thread",
            "Nothing: the dump is wrong, because a RUNNABLE thread always uses CPU",
        ],
        "answer": 1,
        "why": "The JVM can't see inside native code, so a thread in a native socket read counts as RUNNABLE. Its CPU time didn't move in 5 seconds, so it isn't computing: the kernel has it asleep until data arrives. A busy loop would add thousands of milliseconds of CPU, and a deadlock shows BLOCKED or parked threads with lock lines.",
    },
    "sections": [
        {"h": "A thread dump is every stack, printed at one safepoint", "body": S1,
         "try": {"title": "Take your first dump", "minutes": 5,
                 "steps": [
                     "Run the demo. It prints its PID and stays frozen for 120 seconds (pass `-Pargs=300` for longer).",
                     "In a second terminal, run `jcmd` to confirm the PID, then `jcmd <pid> Thread.print -l > dump-1.txt`.",
                     "Predict before you look: which state will the four `report-worker` threads be in, and at which line of `FrozenService.kt`?",
                     "Open `dump-1.txt`. Find the four `report-worker` threads, their state line, their first frame in `workbench.performance.l08` and the address they wait for. Then search for `vt-report`.",
                 ],
                 "code": demo("FrozenService", "FrozenServiceJava"),
                 "expect": "The four `report-worker` threads are `BLOCKED (on object monitor)` in `writeReport` at `FrozenService.kt:54`, and all of them wait to lock the same address. There's no `main` thread (it returned) and no `vt-report` at all: `Thread.print` lists only platform threads. Section 4 deals with the virtual ones. In the Java version the line numbers differ, and the frames say `FrozenServiceJava`."},
         "refs": [{"title": "The jcmd command (JDK 25)", "url": "https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html", "kind": "docs"}]},
        {"h": "RUNNABLE doesn't mean busy: compare cpu= between dumps", "body": S2,
         "try": {"title": "Find the hot thread two ways", "minutes": 4,
                 "steps": [
                     "With the demo still running, take a second dump about 5 seconds after the first: `jcmd <pid> Thread.print -l > dump-2.txt`.",
                     "Predict: which of `catalog-refresh` and `index-rebuild` will show more CPU in the second dump?",
                     "Run the two `grep` lines below and work out how much CPU each thread used between the dumps.",
                     "On Linux, run `top -H -p <pid>` and match the busy thread's PID to a `nid=` in the dump.",
                 ],
                 "code": {"lang": "bash", "title": "terminal 2",
                          "src": "grep -h '^\"index-rebuild\"' dump-1.txt dump-2.txt | grep -o 'cpu=[0-9.]*ms elapsed=[0-9.]*s'\ngrep -h '^\"catalog-refresh\"' dump-1.txt dump-2.txt | grep -o 'cpu=[0-9.]*ms elapsed=[0-9.]*s'\ntop -H -b -n 1 -w 120 -p <pid> | head -12     # Linux only",
                          "run": ""},
                 "expect": "`index-rebuild` gains nearly as many milliseconds of CPU as milliseconds pass on a quiet machine, so it uses close to a whole core; on the busy course machine it got about 39%. `catalog-refresh` shows the same `cpu=` both times, although it is RUNNABLE. In `top -H`, the top line is `index-rebuild`, and its PID equals its `nid=` in the dump."},
         "refs": [{"title": "ThreadMXBean: per-thread CPU time from inside the JVM", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.management/java/lang/management/ThreadMXBean.html", "kind": "docs"}]},
        {"h": "Follow the lock to the thread that holds everyone up", "body": S3,
         "figure": {"svg": FIG, "caption": "Four BLOCKED workers, one lock, one owner. The owner is RUNNABLE but uses no CPU: it's waiting on a socket with the lock held."},
         "try": {"title": "Find an owner with and without -l", "minutes": 4,
                 "steps": [
                     "Take a dump without `-l`: `jcmd <pid> Thread.print > plain.txt`.",
                     "Find `archive-reader`, copy the address on its `parking to wait for` line, and search `plain.txt` for that address. Can you find the owner?",
                     "Now search `dump-1.txt` (taken with `-l`) for the same address.",
                     "Run the `awk` line below on `dump-1.txt`, with the address the `report-worker` threads wait for. It prints the name of the thread that holds it.",
                 ],
                 "code": {"lang": "bash", "title": "terminal 2",
                          "src": "jcmd <pid> Thread.print > plain.txt\ngrep -n 'ReentrantLock' plain.txt dump-1.txt\n# who holds a monitor? print the thread whose stack has \"- locked <address>\"\nawk '/^\"/ { name = $1 } /- locked <0x0000000735c08070>/ { print name }' dump-1.txt",
                          "run": ""},
                 "expect": "In `plain.txt` the address appears only under `archive-reader`: nothing says who owns it. In `dump-1.txt` it also appears under `archive-writer`'s `Locked ownable synchronizers`. The `awk` line prints `\"catalog-refresh\"`. Use the address from your own dump; it changes on every run."},
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
                 "expect": "Two groups: 10,000 threads at `FrozenService.kt:44` (waiting for a permit) and 200 at line 45 (asleep). On JDK 25 the state count says `10000 WAITING` and `200 TIMED_WAITING`. On JDK 21 the plain format has no state field, so the second count doesn't work."},
         "refs": [{"title": "HotSpotDiagnosticMXBean.dumpThreads (JDK 25)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/jdk.management/com/sun/management/HotSpotDiagnosticMXBean.html", "kind": "docs"}]},
    ],
    "compare": {
        "title": "The cpu= column from inside the process, with ThreadMXBean",
        "java": {"title": "HotThreadsJava.java", "src": read(f"{lab}/demo/{J}/HotThreadsJava.java")},
        "kotlin": {"title": "HotThreads.kt", "src": read(f"{lab}/demo/{K}/HotThreads.kt")},
        "note": "Both read the same JVM counters that a dump prints as `cpu=`: sample every thread's CPU time, wait, sample again, and sort by the difference. That's a cheap health check that answers \"which thread is hot\" without `top`. The behavior is the same. Kotlin's `associateWith` and `mapNotNull` replace the two loops, and since `LongArray` has no `mapNotNull`, the Kotlin version calls `toList()` first. One limit applies to both, checked on JDK 21 and 25: `getAllThreadIds()` lists only platform threads, and `getThreadCpuTime` returns -1 for a virtual thread. For virtual threads, look at the carrier threads' CPU, or use a profiler.",
    },
    "worked": {
        "title": "Three dumps of a frozen service, read in five minutes",
        "steps": [
            {"say": "1. Capture the evidence before anyone restarts anything: three dumps, 5 seconds apart, each in its own file.",
             "code": "PID=$(pgrep -f FrozenService | head -1)\nfor i in 1 2 3; do jcmd $PID Thread.print -l > dump-$i.txt; sleep 5; done", "lang": "bash"},
            {"say": "2. Count the states to see the shape. Four BLOCKED threads in a service that should never wait long for a monitor is the first lead. The 12 RUNNABLE ones include JVM threads and threads in native calls, so they prove nothing yet.",
             "code": "grep -h 'java.lang.Thread.State' dump-1.txt | sort | uniq -c | sort -rn\n#   12    java.lang.Thread.State: RUNNABLE\n#    6    java.lang.Thread.State: WAITING (parking)\n#    4    java.lang.Thread.State: BLOCKED (on object monitor)\n#    3    java.lang.Thread.State: TIMED_WAITING (parking)\n#    ...", "lang": "bash"},
            {"say": "3. Ask what the BLOCKED threads want. One address four times means one door and one queue.",
             "code": "grep -h 'waiting to lock' dump-1.txt | sort | uniq -c\n#    4 \t- waiting to lock <0x0000000735c08070> (a java.lang.Object)", "lang": "bash"},
            {"say": "4. Find who holds it, then check whether the owner is working or waiting. Its stack ends in a socket read, and its CPU time is the same in all three dumps: it's waiting for the network with the lock held.",
             "code": "awk '/^\"/ { name = $1 } /- locked <0x0000000735c08070>/ { print name }' dump-1.txt\n# \"catalog-refresh\"\ngrep -h '^\"catalog-refresh\"' dump-*.txt | grep -o 'cpu=[0-9.]*ms'\n# cpu=25.09ms\n# cpu=25.09ms\n# cpu=25.09ms", "lang": "bash"},
            {"say": "5. Fix the owner, not the queue. Make the slow call with a deadline and no lock held, then take the lock only to swap in the result. Now a slow store delays one refresh, not every report.",
             "code": "CatalogData fresh = store.fetchCatalog(Duration.ofSeconds(2));   // 1. slow call: no lock held, with a deadline\nsynchronized (catalog) {                                          // 2. lock only to swap the data\n    catalog.replace(fresh);\n}",
             "lang": "java",
             "alt_code": "val fresh = store.fetchCatalog(Duration.ofSeconds(2))   // 1. slow call: no lock held, with a deadline\nsynchronized(catalog) {                                  // 2. lock only to swap the data\n    catalog.replace(fresh)\n}",
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
            "Open `src/test/resources/workbench/performance/l08/dump-1.txt`. It's a real dump of `FrozenService` on JDK 25, and `dump-2.txt` and `dump-3.txt` were taken about 5 and 11 seconds later. The two `deadlock` files come from a small program with two threads, `merge-A` and `merge-B`, that each lock one chapter and wait for the other's, plus two threads that are both called `worker`.",
            "Run the tests: ten of the eleven fail (the one that checks the given parser passes). Write `hottest`: pair each thread in `after` with the same thread in `before` by `nid`, keep the ones whose CPU grew, biggest first, at most `n`. Run the tests: the three `hottest` tests should pass.",
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
        "Take three dumps a few seconds apart: same frames and flat CPU means stuck, same frames and rising CPU means hot, and no frames of yours means idle. Virtual threads only appear in `Thread.dump_to_file`; group them by your first frame.",
        "The limit: a dump shows who waits and for whom, at one moment. It can't say why the other side doesn't answer or how long calls took; that's what recordings (lesson 5) are for.",
    ],
    "closing": """We started with three photos of a kitchen where nothing moved: waiters queued for the order book, a cook at the back door holding it, another stirring without end. The service's dumps said the same: four BLOCKED workers, a RUNNABLE owner with flat CPU, one hot loop.

That closes the track, which began with a new cook reading every recipe card line by line. We watched the JIT learn, measured it fairly, and found where a running program spends its time and where it waits.

Now search your code for a `synchronized` block or `lock()` that calls the network before letting go.

Next, we'll look at a program's first seconds: why does a JVM start slowly, and how do you measure it?""",
    "quiz": [
        {"q": "A dump shows 30 threads `WAITING (parking)` with `- parking to wait for <0x...> (a java.util.concurrent.locks.ReentrantLock$NonfairSync)`, all the same address. No thread's stack shows `- locked` with that address. What do you do next?",
         "options": [
             "Conclude the lock is free and the dump caught a hand-over",
             "Take the dump again with `-l` and look for the address under some thread's `Locked ownable synchronizers`",
             "Restart the service, since parked threads can't be diagnosed",
             "Look for `Found one Java-level deadlock`, because parked threads always mean a deadlock",
         ],
         "answer": 1,
         "why": "A `ReentrantLock` isn't tied to a stack frame, so its owner never prints `- locked`. With `-l`, each thread lists the `java.util.concurrent` locks it owns, and that's where the owner shows up. A free lock wouldn't keep 30 threads parked, and parked threads are often queued behind a slow owner, not deadlocked."},
        {"q": "`top -H -p 4100` on a JDK 25 service shows thread PID 4187 at 100% CPU. How do you find it in the dump?",
         "options": [
             "Convert 4187 to hex and search for `nid=0x105b`",
             "Search for `#4187`, the Java thread number",
             "Search for `nid=4187` or `[4187]` in the header lines",
             "You can't: top's thread ids aren't in thread dumps",
         ],
         "answer": 2,
         "why": "The `top -H` PID is the Linux thread id, which the dump prints as `nid=` and in brackets. Since JDK 18 it's printed in decimal, so search for it as it is. Converting to hex was needed on JDK 17 and older. `#N` is the Java thread id, a different number."},
        {"q": "Three dumps 5 seconds apart. Thread `export-worker-2` is in `LinkedBlockingQueue.take` under `ThreadPoolExecutor.getTask` in all three, with the same CPU time, and no frame from your code. What is it?",
         "options": [
             "Stuck: same frames and flat CPU in every dump",
             "Hot: it never leaves that frame",
             "Deadlocked with the thread that should put work on the queue",
             "Idle: a pool worker waiting for a task, which is normal",
         ],
         "answer": 3,
         "why": "Same frames and flat CPU fit both stuck and idle. What decides it is whose code is waiting. With no frame of yours, it's the pool's own loop waiting for the next task. It parks on a condition object, which has no owner, so there's nobody to follow. Stuck threads have your code in the stack, waiting for something your code asked for."},
        {"q": "Your service runs 8,000 requests on virtual threads. `jcmd <pid> Thread.print` shows about 40 threads and none of your request code. Why?",
         "options": [
             "`Thread.print` lists platform threads only. Use `jcmd <pid> Thread.dump_to_file`, which includes virtual threads",
             "The requests already finished",
             "Virtual threads have no stacks until they run",
             "You need `-l` to see virtual threads",
         ],
         "answer": 0,
         "why": "The classic dump lists platform threads, so you see the carrier threads but not the virtual threads on them. JEP 444 added `Thread.dump_to_file` (plain or JSON), which includes virtual threads, running or parked. `-l` only adds lock ownership to the classic dump."},
        {"q": "A hot thread's dump shows its top frame at the end of a short loop in `buildSummary`, but async-profiler puts most of its CPU in `String.split`, which `buildSummary` calls inside that loop. Which is right, and why?",
         "options": [
             "The dump: it's taken from the real thread, so its top frame is exact",
             "Neither: both tools sample at random",
             "async-profiler: a thread dump stops threads at safepoint polls, such as the jump back in a loop, so it reports where the thread reached the next poll",
             "The dump, because async-profiler can't see inlined methods",
         ],
         "answer": 2,
         "why": "A thread dump is taken at a safepoint, so it has the safepoint bias from lesson 6: a hot thread is caught at its next poll, often a loop's jump back or a method return, not at the instruction that costs the most. async-profiler interrupts the thread wherever it is, and it does show inlined frames. Use dumps to find which thread is hot, and a profiler to find where its time goes.",
         "from": "perf-06"},
    ],
    "flashcards": [
        {"front": "A thread is RUNNABLE in `SocketDispatcher.read0` and its `cpu=` doesn't change between dumps. What is it doing?", "back": "Waiting for bytes from the network. The JVM reports threads in native code as RUNNABLE; the operating system has it asleep."},
        {"front": "How do you tell a hot thread from a stuck one, with only thread dumps?", "back": "Take two dumps a few seconds apart and compare `cpu=`. Same frames and rising CPU is hot; same frames and flat CPU is stuck."},
        {"front": "`top -H` shows thread 25047 busy. Where is it in a JDK 18+ dump?", "back": "Search for `nid=25047`. Since JDK 18 the nid is decimal; JDK 17 and older print it in hex."},
        {"front": "Which `jcmd` option shows who owns a `ReentrantLock`?", "back": "`Thread.print -l`. It lists each thread's `Locked ownable synchronizers`. Without it, only the waiters show."},
        {"front": "What does `- waiting on <a>` mean, compared with `- waiting to lock <a>`?", "back": "`waiting on`: inside `Object.wait()`, with the monitor given back. `waiting to lock`: BLOCKED, trying to enter `synchronized` on `a`."},
        {"front": "Your virtual threads don't appear in `jcmd <pid> Thread.print`. What do you run instead?", "back": "`jcmd <pid> Thread.dump_to_file <file>` (add `-format=json` for tools). Then group the threads by their first frame of your code."},
        {"front": "Why can't you match a lock address like `<0x0000000735c08070>` across two dumps?", "back": "It's the object's heap address at that moment, and a GC can move the object between dumps. It's reliable only within one dump."},
    ],
    "terms": [
        {"term": "thread dump", "plain": "A printout of every thread's name, state, stack and locks at one moment."},
        {"term": "safepoint", "plain": "A point where the JVM knows the full state of every frame, so it can stop a thread there and read its stack."},
        {"term": "nid", "plain": "The operating system's thread id in a dump header. It's the PID column of `top -H`."},
        {"term": "monitor", "plain": "The lock that `synchronized` takes on an object. A dump shows it as `- locked <address>`."},
        {"term": "ownable synchronizer", "plain": "A `java.util.concurrent` lock, such as `ReentrantLock`, that a thread owns. `Thread.print -l` lists them per thread."},
        {"term": "carrier thread", "plain": "A platform thread that runs virtual threads. A classic dump shows the carriers but not the virtual threads."},
    ],
    "explain_back": {
        "prompt": "Explain to a teammate how you'd find out why a service has stopped answering, using only thread dumps. Say what you'd capture, what you'd compare, and how you'd decide which thread to fix.",
        "answer": "Before anyone restarts it, I'd take three dumps with `jcmd <pid> Thread.print -l`, 5 seconds apart. In each thread I read the name, the state, the first frame of our code and the lock lines. I don't trust RUNNABLE, because threads in native socket reads are RUNNABLE too, so I compare `cpu=` between dumps. A thread whose CPU rises in the same frame is hot. For blocked or parked threads I follow the lock: the address on `waiting to lock` or `parking to wait for` leads to the thread that holds it, under `- locked` or, for a `ReentrantLock`, under `Locked ownable synchronizers`. I keep following until I reach a thread that waits for something outside the JVM, like a socket, or until the chain loops, which is a deadlock. That owner is what I fix. Threads with the same frames, flat CPU and none of our code are just idle pool threads. On virtual threads I'd use `Thread.dump_to_file`, group the threads by their first frame, and read the biggest group.",
    },
    "deeper": {
        "minutes": 10,
        "body": """The JSON format is what you'd feed a tool. On JDK 25 each thread has `tid`, `name`, `state`, `stack`, and lock fields: `parkBlocker` with the parked-on object and its `owner` thread id, `blockedOn` for a monitor a thread wants, `waitingOn`, and `monitorsOwned`. On JDK 21 a thread has only `tid`, `name` and `stack`. The JSON also groups threads by **thread container**: `<root>`, each thread pool, and each executor made by `Executors.newVirtualThreadPerTaskExecutor()`. In this lesson's demo, `<root>` holds 10,212 threads, because the demo starts its virtual threads with `Thread.ofVirtual()` directly, and each `ThreadPoolExecutor` holds its own workers. With virtual threads, that grouping often says more than the stacks do.

```bash
jcmd <pid> Thread.dump_to_file -format=json /tmp/threads.json
jq '.threadDump.threadContainers[] | {container, threadCount}' /tmp/threads.json
```

`Thread.print -e` adds `allocated=` and `defined_classes=` to each header. That's another cheap way, besides JFR, to find the thread that allocates the most.

If the JVM is so stuck that it can't reach a safepoint, `jcmd` and `kill -3` both hang, because both need one. The last resort is `jhsdb jstack --pid <pid>`. It reads the process from outside, like a debugger, so it needs permission to attach to the process (ptrace on Linux) and pauses the whole JVM while it reads. Use it only when the normal dump won't come.

In code, `ThreadMXBean.dumpAllThreads(true, true)` returns the same information as `Thread.print -l` as `ThreadInfo` objects, and `findDeadlockedThreads()` runs the deadlock check. Both cover platform threads only. A health check that runs `findDeadlockedThreads()` every minute costs a safepoint each time. On this busy machine one `Thread.print` safepoint took 36 to 74 ms, so measure before you add one to a service where every millisecond counts.""",
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
