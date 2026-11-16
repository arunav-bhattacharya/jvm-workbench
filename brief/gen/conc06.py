import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/concurrency/src"
P = "java/workbench/concurrency/l06"
K = "kotlin/workbench/concurrency/l06"
read = lambda p: (ROOT / p).read_text()
demo = lambda name: f"./gradlew :concurrency:demo -Pmain=workbench.concurrency.l06.{name}"
def kt(name, run_args=""):
    """The Kotlin twin of a Java demo: Foo.kt with a top-level main, class FooKt."""
    return {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{K}/{name}.kt"),
            "run": demo(f"{name}Kt") + run_args, "file": f"{lab}/demo/{K}/{name}.kt"}
def pair(java, kotlin):
    """A Java fence followed by its Kotlin twin, as the brief asks."""
    return f"```java\n{java}\n```\n\n```kotlin\n{kotlin}\n```"

SIM = {
 "title": "Two transfers, two locks, opposite orders",
 "intro": "T1 runs transfer(a, b), T2 runs transfer(b, a). First let them finish one after the other. Then reset and find the order that freezes both.",
 "vars": {"transfers": 0},
 "locks": ["a", "b"],
 "threads": [
  {"name": "T1: transfer(a, b)", "steps": [
   {"op": "lock", "lock": "a", "code": "synchronized (a) {"},
   {"op": "lock", "lock": "b", "code": "    synchronized (b) {"},
   {"op": "read", "var": "transfers", "reg": "r", "code": "        int r = transfers;"},
   {"op": "add", "reg": "r", "n": 1, "code": "        r = r + 1;   // move the money"},
   {"op": "write", "var": "transfers", "reg": "r", "code": "        transfers = r;"},
   {"op": "unlock", "lock": "b", "code": "    }"},
   {"op": "unlock", "lock": "a", "code": "}"}]},
  {"name": "T2: transfer(b, a)", "steps": [
   {"op": "lock", "lock": "b", "code": "synchronized (b) {"},
   {"op": "lock", "lock": "a", "code": "    synchronized (a) {"},
   {"op": "read", "var": "transfers", "reg": "r", "code": "        int r = transfers;"},
   {"op": "add", "reg": "r", "n": 1, "code": "        r = r + 1;   // move the money"},
   {"op": "write", "var": "transfers", "reg": "r", "code": "        transfers = r;"},
   {"op": "unlock", "lock": "a", "code": "    }"},
   {"op": "unlock", "lock": "b", "code": "}"}]}
 ],
 "goal": {"var": "transfers", "eq": 2, "say": "Both transfers finished. Now reset and give each thread its first lock before either takes its second."}
}

FIG = (
    '<svg viewBox="0 0 640 240" role="img" aria-label="Wait-for cycle: T1 holds lock a and waits for lock b; T2 holds lock b and waits for lock a">'
    '<rect class="box-a" x="30" y="92" width="160" height="56" rx="8"/>'
    '<text class="t" x="110" y="115" text-anchor="middle">T1</text><text class="t-s t-code" x="110" y="135" text-anchor="middle">transfer(a, b)</text>'
    '<rect class="box-b" x="450" y="92" width="160" height="56" rx="8"/>'
    '<text class="t" x="530" y="115" text-anchor="middle">T2</text><text class="t-s t-code" x="530" y="135" text-anchor="middle">transfer(b, a)</text>'
    '<rect class="box" x="250" y="16" width="140" height="44" rx="8"/><text class="t t-code" x="320" y="43" text-anchor="middle">lock a</text>'
    '<rect class="box" x="250" y="180" width="140" height="44" rx="8"/><text class="t t-code" x="320" y="207" text-anchor="middle">lock b</text>'
    '<line class="ln" x1="250" y1="44" x2="185" y2="90" marker-end="url(#arr)"/><text class="t-s" x="205" y="56" text-anchor="end">held by</text>'
    '<line class="ln-bad" x1="185" y1="150" x2="250" y2="196" marker-end="url(#arr)"/><text class="t-s t-bad" x="205" y="190" text-anchor="end">waits for</text>'
    '<line class="ln" x1="390" y1="196" x2="455" y2="150" marker-end="url(#arr)"/><text class="t-s" x="435" y="190" text-anchor="start">held by</text>'
    '<line class="ln-bad" x1="455" y1="90" x2="390" y2="44" marker-end="url(#arr)"/><text class="t-s t-bad" x="435" y="56" text-anchor="start">waits for</text>'
    '<text class="t t-bad" x="320" y="118" text-anchor="middle">a cycle:</text><text class="t-s t-bad" x="320" y="136" text-anchor="middle">nobody can move</text>'
    '</svg>'
)

# Real output: DeadlockDemo -Pargs=wait, then jcmd <pid> Thread.print, on JDK 21.0.12.1 (trimmed).
HEADERS = """"transfer-A-to-B" #19 ... cpu=1.79ms elapsed=34.69s ... waiting for monitor entry
   java.lang.Thread.State: BLOCKED (on object monitor)
"transfer-B-to-A" #20 ... cpu=1.40ms elapsed=34.69s ... waiting for monitor entry
   java.lang.Thread.State: BLOCKED (on object monitor)"""

DUMP = """Found one Java-level deadlock:
=============================
"transfer-A-to-B":
  waiting to lock monitor 0x00007fb14c0019a0 (object 0x00000006f794b518, a java.lang.Object),
  which is held by "transfer-B-to-A"

"transfer-B-to-A":
  waiting to lock monitor 0x00007fb150000fe0 (object 0x00000006f794b508, a java.lang.Object),
  which is held by "transfer-A-to-B"

Java stack information for the threads listed above:
===================================================
"transfer-A-to-B":
	at workbench.concurrency.l06.DeadlockDemo.move(DeadlockDemo.java:42)
	- waiting to lock <0x00000006f794b518> (a java.lang.Object)
	- locked <0x00000006f794b508> (a java.lang.Object)
	...
"transfer-B-to-A":
	at workbench.concurrency.l06.DeadlockDemo.move(DeadlockDemo.java:42)
	- waiting to lock <0x00000006f794b508> (a java.lang.Object)
	- locked <0x00000006f794b518> (a java.lang.Object)
	...

Found 1 deadlock."""

J_BAD = """// Naive: correct alone, freezes in pairs
void transfer(Account from, Account to, long cents) {
    synchronized (from) {
        synchronized (to) {
            from.debit(cents);
            to.credit(cents);
        }
    }
}
// thread 1: transfer(a, b, 100)        thread 2: transfer(b, a, 50)"""
K_BAD = """// Naive: correct alone, freezes in pairs
fun transfer(from: Account, to: Account, cents: Long) {
    synchronized(from) {
        synchronized(to) {
            from.debit(cents)
            to.credit(cents)
        }
    }
}
// thread 1: transfer(a, b, 100)        thread 2: transfer(b, a, 50)"""
J_ORDER = """// Fixed: every transfer locks the lower id first
void transfer(Account from, Account to, long cents) {
    Account first = from.id() < to.id() ? from : to;   // one order for everyone
    Account second = first == from ? to : from;
    synchronized (first) {
        synchronized (second) {
            from.debit(cents);
            to.credit(cents);
        }
    }
}"""
K_ORDER = """// Fixed: every transfer locks the lower id first
fun transfer(from: Account, to: Account, cents: Long) {
    val first = if (from.id < to.id) from else to      // one order for everyone
    val second = if (first === from) to else from
    synchronized(first) {
        synchronized(second) {
            from.debit(cents)
            to.credit(cents)
        }
    }
}"""
J_TRY = """if (from.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
    try {
        if (to.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
            try { /* move the money */ return true; }
            finally { to.lock().unlock(); }
        }
    } finally {
        from.lock().unlock();      // couldn't get both: let go of everything
    }
}
Thread.sleep(ThreadLocalRandom.current().nextLong(1, 10));   // random back-off, then retry"""
K_TRY = """if (from.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
    try {
        if (to.lock().tryLock(10, TimeUnit.MILLISECONDS)) {
            try { /* move the money */ return true }
            finally { to.lock().unlock() }
        }
    } finally {
        from.lock().unlock()       // couldn't get both: let go of everything
    }
}
Thread.sleep(ThreadLocalRandom.current().nextLong(1, 10))    // random back-off, then retry"""

J_DRILL = """void transfer(Account from, Account to, long cents) {
    Account first = from.id() < to.id() ? from : to;
    Account second = first == from ? to : from;
    first.lock().lock();
    try {
        second.lock().lock();
        try {
            from.debit(cents);
            to.credit(cents);
        } finally {
            second.lock().unlock();
        }
    } finally {
        first.lock().unlock();
    }
}"""
K_DRILL = """fun transfer(from: Account, to: Account, cents: Long) {
    val first = if (from.id < to.id) from else to
    val second = if (first === from) to else from
    first.lock().lock()
    try {
        second.lock().lock()
        try {
            from.debit(cents)
            to.credit(cents)
        } finally {
            second.lock().unlock()
        }
    } finally {
        first.lock().unlock()
    }
}"""


OPENING = """A bank keeps a balance for each account, and a transfer moves money between two accounts. In synchronized and intrinsic locks, every transfer took the same lock, so only one transfer could run at a time. That design is easy to trust, and its one cost is speed: a transfer between two friends waits behind one between two strangers, though they share no account.

So the next version gives each account its own lock, and a transfer takes the two it needs. It passes every test. Then, on a busy day, the program stops answering. The processor goes quiet, with no error and no log line. The JVM knows exactly what happened. It just won't say a word until someone asks.

The kitchen in the last lesson stalled with its lock free. This time, threads (lines of work running side by side in one program) stall while holding locks. In this lesson, we'll freeze two transfers, ask the JVM why, and find the four conditions every such freeze needs. Then we'll break them with one lock order, and with a lock that gives up. Before we start, make a guess, and keep it in mind."""

# ---------------------------------------------------------------- section 0
S0 = """Here's the version with one lock per account. A lock, remember, lets only one thread at a time into the code it guards. Here each account object's built-in lock, its monitor, does the job, and `synchronized` takes it. A transfer locks the account it takes money from, then the account it adds money to, so the two changes still happen as one step:

""" + pair(J_BAD, K_BAD) + """

Each call is correct on its own, and transfers between different pairs of accounts now run side by side, which was the point. The trouble starts when two transfers touch the same two accounts in opposite directions. Picture two friends who keep paying each other back. Ana's account is `a` and Ben's is `b`, and Ana sends Ben 100 for lunch at the same moment Ben sends Ana 50 for the cinema.

Let's trace the smallest case. Thread 1 runs `transfer(a, b, 100)` and locks `a`. At the same moment, thread 2 runs `transfer(b, a, 50)` and locks `b`. Thread 1 now asks for `b`, which thread 2 holds. Thread 2 asks for `a`, which thread 1 holds. Each releases its first lock only after it gets its second, so neither ever will. A third transfer that needs `a` arrives a second later and joins the line behind them, for good.

Those two threads will wait for each other forever: that's a **deadlock**. Nothing throws, and nothing logs. Both threads sit in `BLOCKED`, the state of a thread waiting for a lock. The processor has nothing to do, and every other transfer that needs either account piles up behind them.

The nasty part is timing. Both threads must take their first lock inside the same tiny window, so a test that runs one transfer at a time never sees it. On a busy day, with thousands of transfers a second between the same busy accounts, it's only a matter of when. The simulator below lets you play the scheduler, the part of the system that decides which thread runs next, and find the freeze by hand.

The Try it widens the window with a 300 ms sleep, so it freezes every time. Its last lines come from asking the JVM which threads are deadlocked, and the JVM answers with names. When a real program freezes, you'd ask from outside it, before anyone restarts it. That's next."""

# ---------------------------------------------------------------- section 1
S1 = """A frozen program tempts everyone to restart it. Take a thread dump first. A **thread dump** is a printout of every thread in a running JVM: its name, its state and its stack (the chain of method calls it is in the middle of). The restart brings the program back, and it throws away the only record of why it stopped.

The JDK's `jcmd` tool sends commands to a running JVM. It finds the program by its PID, the process id that the operating system gives each running program:

```bash
jcmd                      # lists Java processes with their PIDs
jcmd <pid> Thread.print   # every thread's state and stack, plus deadlock detection
```

`jstack <pid>`, an older tool, prints the same dump. Each thread starts with a header line and its state. Here are our two transfers, from the demo on JDK 21, trimmed:

```text
""" + HEADERS + """
```

Both threads are `BLOCKED`, and in 35 seconds each one used under 2 ms of CPU time. That's a deadlock seen from outside: threads that exist, hold their locks and do nothing. Asked with `jcmd`, though, the JVM turns out to be a very precise witness. When it finds a cycle of threads waiting for each other's locks, it says so near the end of the dump:

```text
""" + DUMP + """
```

Read it from the bottom up. Each thread's stack shows what it holds (`- locked <...>`) and what it wants (`- waiting to lock <...>`). The report above the stacks names who holds the lock it wants. Follow the two addresses and you've drawn the cycle: `...b508` is held by the first thread and wanted by the second, and `...b518` the other way round. Both stacks point at `DeadlockDemo.java:42`, the inner `synchronized`.

The detector finds deadlocks on `ReentrantLock` too. That's a lock object, used by the lab's accounts, that you take by calling `lock()` and release by calling `unlock()`. There the dump says `waiting for ownable synchronizer ... which is held by`, and the stacks show `parking to wait for` instead of `waiting to lock`. Those threads are parked (put to sleep until the lock comes free), so they show `WAITING (parking)`, not `BLOCKED`. Don't search a dump for `BLOCKED` alone. `Thread.print -l` also lists the `java.util.concurrent` locks each thread owns.

Inside the program, the same question is one call to `ThreadMXBean`, the JDK's window onto the JVM's threads. It's the call the demo made:

""" + pair("long[] ids = ManagementFactory.getThreadMXBean().findDeadlockedThreads();   // null if none",
           "val ids: LongArray? = ManagementFactory.getThreadMXBean().findDeadlockedThreads()   // null if none") + """

If you write web services, this call makes a cheap health check: a small test the service runs on itself, so whatever watches it can see that it's stuck.

Two limits to know. The detector only sees cycles of Java locks. A program that uses a database often keeps a pool of open connections that threads borrow and give back. Twenty threads that each hold one of 20 pooled connections and wait for a second one are deadlocked too, but the dump shows only twenty threads waiting inside the pool. And Java Flight Recorder (JFR), the event recorder built into the JVM, has no deadlock event, so thread dumps and `ThreadMXBean` are how you find them.

The dump tells us what happened: two threads, two locks, one cycle. To stop it happening, we need to know why a cycle can form at all."""

ASIDE1 = {
    "title": "If the JVM can find the cycle, why doesn't it break it?",
    "body": "Because nothing it could do would be safe. Breaking a deadlock means taking a lock away from a thread in the middle of its critical section (the code it runs under the lock), and that leaves half-changed data behind. It's the same reason `Thread.stop()` was removed from Java. A database can do it, because it can undo unfinished work, which is called rolling it back. Oracle, a widely used database, for example, fails one of the deadlocked statements with error `ORA-00060` and lets your code retry. A Java method has no rollback, and the Java Language Specification says outright that Java neither prevents deadlock nor requires the JVM to detect it. So the fix has to live in your code."
}

# ---------------------------------------------------------------- section 2
S2 = """Look back at the dump and you'll find four things true at once. Together they're known as the Coffman conditions, after a 1971 paper. Each one is about a resource, which means anything a thread must hold to get its work done, such as a lock:

1. **Mutual exclusion.** A resource can be held by only one thread at a time. Each of our locks had one owner.
2. **Hold and wait.** A thread holds one resource while it waits for another, as each transfer held its first account.
3. **No preemption.** Nobody can take a resource away from the thread that holds it (taking it away is called preemption), so neither transfer could take the other's lock.
4. **Circular wait.** There's a cycle: T1 waits for T2, which waits for T1, just as the dump showed. Longer cycles count too.

Take away any one of the four, and a deadlock can't form. The figure draws our cycle as a **wait-for graph**: an arrow from each thread to the lock it wants, and from each lock to the thread that holds it. A deadlock is a loop in that graph, and that loop is what the JVM's detector looks for.

**A deadlock needs all four conditions. Break any one, and it can't happen.**

In practice you pick one of three moves. A **global lock order** breaks circular wait, and the next section builds it. A **timed lock** breaks no preemption: a thread that can't get its second lock in time gives back the first, and the last section takes that one. **Needing only one lock** breaks hold and wait, as the one-lock bank we started from did. Mutual exclusion is the one you rarely remove, since it's the reason you took a lock. Data that never changes, or one owning thread per account (lesson 11 of this track), can still design it away.

The four conditions apply to any resource, not only Java locks. Test the model on the kitchen from the last lesson, with 20 cooks and 20 pans. Every dish needs two pans, so each cook grabs one pan and then reaches for a second. Which conditions hold, and which move would you pick? (All four hold, and once every pan is taken, every cook waits forever. Taking both pans in one step, or cooking with one, breaks hold and wait. A rule that a cook who can't get a second pan within a minute puts the first one back breaks no preemption.)

Of the three moves, a lock order costs the least, so let's start there."""

# ---------------------------------------------------------------- section 3
S3 = """Circular wait needs two threads that disagree about which lock comes first. So let's make them agree. Give every account a stable, unique key, and always lock the lower key first, whichever way the money moves:

""" + pair(J_ORDER, K_ORDER) + """

Read the two lines that pick the locks as a sentence: the first lock is the account with the lower id, and the second is the other one. Now `transfer(a, b)` and `transfer(b, a)` both lock `a` first. Whoever gets `a` runs. The other waits for `a` while holding nothing. That's plain contention, threads taking turns at a lock: it waits its turn, then goes.

The Try it below runs the exact traffic that froze the naive version: 200,000 transfers between the same two accounts, half in each direction. Correctness first: the total stayed at 2,000,000. Then time: it finished in 33 to 50 ms on runs here. With the locks put back in argument order (`from` first, then `to`), it hung on five runs out of six, anywhere from about 1,500 to 53,000 transfers in. The sixth run finished, which is the same bug, hiding.

Three details make or break the fix.

The key must be unique and must never change. An account number works. `hashCode()` doesn't: two different objects can share one, and then two threads may disagree about the order again.

The rule must be global, which means all the code follows it. Each method locking in a sensible-looking order isn't enough. One method that locks the account and then the customer, and another that locks the customer and then the account, rebuild the cycle. Put the ordering in one helper method and make every caller use it.

**A lock order only works if every caller follows it. Write it once, and use it everywhere.**

The order must also survive calls you don't see. Alien code, meaning code you don't control such as a listener, may take locks of its own, in its own order, if you call it while you hold a lock. That's the alien-code rule from synchronized and intrinsic locks, and the worked example below finds a deadlock hiding exactly there.

If you keep accounts in a database, the same rule applies there. Two database transactions that lock the same two account rows in opposite orders deadlock too. (A transaction is a group of changes that succeed or fail together.) Locking rows in account-number order cures it.

A lock order works when you know every lock up front. Sometimes you don't, for example when the second account is known only after you've read the first. For that, we need a lock that can give up."""

# ---------------------------------------------------------------- section 4
S4 = """Every lock so far waits as long as it takes, which is the no-preemption condition at work. `ReentrantLock`, the lock in the lab's `Account` class, offers a way out. Like `synchronized`, its `lock()` waits until the lock is free. Unlike it, `tryLock(10, TimeUnit.MILLISECONDS)` waits at most 10 ms and returns `false` if the lock is still taken. (The next lesson covers `ReentrantLock` in full.) So a transfer can try for both locks, and let go if it can't get them:

""" + pair(J_TRY, K_TRY) + """

First we try the account we take money from, for 10 ms. If we get it, we try the other one, for 10 ms more. If both succeed, the money moves and we return. If the second fails, the `finally` gives back the first, so we hold nothing while we wait to retry. That release is the whole fix: a thread that can't finish lets go of everything.

The random back-off on the last line, a short pause before trying again, matters more than it looks. Leave it out, or sleep a fixed time, and two threads can fall into step: both take their first lock, both fail on the second, both release, and both retry at the same moment, over and over. That's **livelock**. The threads are busy and change state all the time, and nothing gets done. A thread dump looks healthy, which makes livelock harder to spot than deadlock.

The Try it shows a livelock with no locks at all. Picture two very polite diners at a table with one spoon. Both are hungry, and each hands the spoon over whenever the other is hungry too. In one second, the demo's diners passed it about 6 million times. Nobody ate. The fix is to break the symmetry: a random back-off, or a rule such as "after three polite turns, eat anyway". With that rule, they passed the spoon 6 times and both diners ate.

**Two threads that retry in step can retry forever. Back off for a random time.**

The third failure is **starvation**: the program makes progress, but one thread never does. A `ReentrantLock` is non-fair by default, so a thread that just released it can take it again before a waiting thread wakes up. That's faster overall, but one unlucky thread can wait a long time. A fair lock, `new ReentrantLock(true)`, serves the longest-waiting thread first instead, at some cost in throughput, the work done per second. A writer (a thread that changes shared data) that never gets past a crowd of readers (threads that only look at it) starves the same way, and lesson 12 of this track comes back to that.

A timeout, a lock that gives up and a fair queue are all things `synchronized` can't offer. They come from the explicit locks, and the second part of the lab puts `tryLock` to work."""

L = {
 "id": "conc-06",
 "title": "Deadlock, livelock and starvation",
 "minutes": 38,
 "goal": "By the end you can explain the four conditions for deadlock, remove one with lock ordering or timed `tryLock`, tell deadlock from livelock and starvation, and find a deadlock in a thread dump.",
 "opening": OPENING,
 "warmup": {
  "q": "`transfer(from, to)` locks `from`, then `to`. One thread runs `transfer(a, b)` while another runs `transfer(b, a)`, many times. What is the worst that can happen?",
  "options": ["A few transfers run slower because they wait for each other", "Money is lost, because the two transfers race on the balances", "Both threads stop for good, each holding one lock and waiting for the other", "The JVM detects the problem and throws a DeadlockException"],
  "answer": 2,
  "why": "If each thread takes its first lock before the other takes its second, T1 holds `a` and waits for `b` while T2 holds `b` and waits for `a`. Neither can ever move. The balances stay correct, because the locks still exclude each other, but nothing progresses. Java has no DeadlockException: the threads just sit there, BLOCKED, until someone restarts the program. The first section traces it step by step."
 },
 "sections": [
  {
   "h": "One lock per account, and two transfers that freeze each other",
   "body": S0,
   "sim": SIM,
   "try": {
    "title": "Freeze two transfers",
    "minutes": 3,
    "steps": [
     "Read `DeadlockDemo`. Each thread takes its first lock, sleeps 300 ms, then asks for the second.",
     "Write down what you expect it to print, then run it. After one second, `main` asks the JVM which threads are deadlocked.",
     "Delete the `sleep(300)` line and run it a few times. Does it still freeze every time?"
    ],
    "code": {"lang": "java", "title": "DeadlockDemo.java", "src": read(f"{lab}/demo/{P}/DeadlockDemo.java"),
             "run": demo("DeadlockDemo"), "file": f"{lab}/demo/{P}/DeadlockDemo.java", "alt": kt("DeadlockDemo")},
    "expect": "With the sleep: `deadlocked threads: 2`, both BLOCKED, each wanting a lock held by the other, and no `moved the money` line. Without the sleep it freezes only sometimes, and often both transfers finish. It's the same bug, now hiding: the sleep only widens a window that is always there."
   }
  },
  {
   "h": "Asking the JVM: a deadlock in a thread dump",
   "body": S1,
   "aside": ASIDE1,
   "try": {
    "title": "Take the dump yourself",
    "minutes": 5,
    "steps": [
     "Run `" + demo("DeadlockDemo") + " -Pargs=wait`. It freezes, prints its PID, and stays alive for 60 seconds.",
     "In a second terminal, run `jcmd <pid> Thread.print` with that PID. Find `Found one Java-level deadlock` and follow each thread's `locked` and `waiting to lock` lines to a line number.",
     "Run `jcmd <pid> Thread.dump_to_file -format=json /tmp/dump.json` and open the file. Which fields does each thread have on your JDK?"
    ],
    "code": {"lang": "bash", "title": "terminal 2", "src": "jcmd                                   # find the PID of DeadlockDemo\njcmd <pid> Thread.print\njcmd <pid> Thread.dump_to_file -format=json /tmp/dump.json", "run": ""},
    "expect": "The text dump ends with `Found 1 deadlock.` and points both threads at `DeadlockDemo.java:42`. The JSON has `tid`, `name` and `stack` per thread on JDK 21, plus state and lock fields on JDK 25 and later. `Thread.dump_to_file` refuses to overwrite an existing file unless you add `-overwrite`."
   },
   "refs": [
    {"title": "diagnosticCommand.hpp at jdk-27-ga: the jcmd Thread.* commands", "url": "https://github.com/openjdk/jdk/blob/jdk-27-ga/src/hotspot/share/services/diagnosticCommand.hpp", "kind": "docs"}
   ]
  },
  {
   "h": "Four conditions every deadlock needs, so break one",
   "body": S2,
   "figure": {"svg": FIG, "caption": "A wait-for graph. Each thread holds one lock and waits for the other's. The loop is the deadlock."}
  },
  {
   "h": "The first fix: every transfer takes the locks in one order",
   "body": S3,
   "try": {
    "title": "Same transfers, one order",
    "minutes": 3,
    "steps": [
     "Read `OrderedLocks`. It runs 100,000 transfers in each direction between the same two accounts, with the ordering rule above.",
     "Predict whether it finishes, then run it.",
     "Break it on purpose: change `move` to lock `from` first and `to` second. Run it again a few times, and stop it with Ctrl+C when it hangs."
    ],
    "code": {"lang": "java", "title": "OrderedLocks.java", "src": read(f"{lab}/demo/{P}/OrderedLocks.java"),
             "run": demo("OrderedLocks"), "file": f"{lab}/demo/{P}/OrderedLocks.java", "alt": kt("OrderedLocks")},
    "expect": "With ordered locks, 200,000 opposite transfers finish in well under a second (33 to 50 ms in runs here), and the total stays 2,000,000. In argument order it usually hangs, often within the first few thousand transfers. With no sleep to widen the window it comes down to luck, so now and then a run survives."
   }
  },
  {
   "h": "A lock that gives up: tryLock, livelock and starvation",
   "body": S4,
   "try": {
    "title": "Watch a livelock, then break the symmetry",
    "minutes": 3,
    "steps": [
     "Run `LivelockDemo`. Both diners are hungry, and both are polite.",
     "Read the count of handovers and meals.",
     "Predict what a rule of \"three polite turns, then eat anyway\" will print. Then run it again with `-Pargs=fixed`."
    ],
    "code": {"lang": "java", "title": "LivelockDemo.java", "src": read(f"{lab}/demo/{P}/LivelockDemo.java"),
             "run": demo("LivelockDemo"), "file": f"{lab}/demo/{P}/LivelockDemo.java", "alt": kt("LivelockDemo")},
    "expect": "Without the fix: millions of handovers in one second (about 5.7 to 6 million in runs here) and `meals eaten: 0`. Both threads were RUNNABLE the whole time. With `-Pargs=fixed`: 6 handovers and 2 meals, done at once."
   }
  }
 ],
 "compare": {
  "title": "Ordered locking in Java and Kotlin",
  "java": {"title": "Java", "src": J_DRILL},
  "kotlin": {"title": "Kotlin", "src": "fun transfer(from: Account, to: Account, cents: Long) {\n    val first = if (from.id < to.id) from else to\n    val second = if (first === from) to else from\n    first.lock().withLock {                 // kotlin.concurrent.withLock: lock, try, finally unlock\n        second.lock().withLock {\n            from.debit(cents)\n            to.credit(cents)\n        }\n    }\n}"},
  "note": "Both versions take the same two locks in the same order, so both are safe for the same reason. Drop the ordering, and both deadlock the same way: Kotlin adds no protection here. One thing differs. Kotlin's `withLock { }` extension on `Lock` writes the `lock()`, the `try` and the `finally` for you, so the release can't go missing. The Java version spells out that discipline by hand, which makes every `lock()` and its matching `finally` easy to check line by line when you read it. `jcmd` is the neutral referee here: both compile to the same `ReentrantLock` calls, and a deadlock in either one produces the same dump."
 },
 "worked": {
  "title": "Find a deadlock that hides behind a callback",
  "steps": [
   {"say": "The bank keeps a `Ledger`, the record of every entry (each amount paid in or out). It also keeps an `AuditLog`, a file that lists recent entries so someone can check them later. Every time the ledger records an entry, it tells the log. Once a second, a timer thread flushes the log: it writes the waiting entries to the file, along with the ledger's current balance. Each class looks fine on its own. Before you read on, find the cycle.",
    "code": "class Ledger {\n    synchronized void post(Entry e) {\n        entries.add(e);\n        auditLog.record(e);              // calls AuditLog while holding the Ledger lock\n    }\n    synchronized long balance() { return sum(entries); }\n}\n\nclass AuditLog {\n    synchronized void record(Entry e) { pending.add(e); }\n    synchronized void flush() {\n        long b = ledger.balance();       // calls Ledger while holding the AuditLog lock\n        write(pending, b);\n        pending.clear();\n    }\n}", "lang": "java",
    "alt_code": "class Ledger(private val auditLog: AuditLog) {\n    @Synchronized fun post(e: Entry) {\n        entries += e\n        auditLog.record(e)               // calls AuditLog while holding the Ledger lock\n    }\n    @Synchronized fun balance(): Long = sum(entries)\n}\n\nclass AuditLog {\n    @Synchronized fun record(e: Entry) { pending += e }\n    @Synchronized fun flush() {\n        val b = ledger.balance()         // calls Ledger while holding the AuditLog lock\n        write(pending, b)\n        pending.clear()\n    }\n}", "alt_lang": "kotlin"},
   {"say": "A teller thread, one serving a customer, is in `post`: it holds the Ledger lock and wants the AuditLog lock. The timer thread is in `flush`: it holds the AuditLog lock and wants the Ledger lock. It's our two transfers again, with the two locks split across two classes. The dump would show it like this:",
    "code": "\"teller-7\":     waiting to lock <0x...a0> (a AuditLog), locked <0x...b8> (a Ledger)\n\"log-flusher\":  waiting to lock <0x...b8> (a Ledger),   locked <0x...a0> (a AuditLog)", "lang": "text"},
   {"say": "You could impose an order, but the cleaner fix is to stop holding one lock while calling the other class. Each method keeps its own lock only around its own state. Before reading the fix, decide: which call in each method is the alien one, the call into code this class doesn't control?",
    "code": "void post(Entry e) {\n    synchronized (this) { entries.add(e); }\n    auditLog.record(e);                  // 1. no Ledger lock held while calling out\n}\n\nvoid flush() {\n    long b = ledger.balance();           // 2. read the balance before taking our own lock\n    List<Entry> batch;\n    synchronized (this) { batch = List.copyOf(pending); pending.clear(); }\n    write(batch, b);                     // 3. slow file writing with no lock at all\n}", "lang": "java",
    "alt_code": "fun post(e: Entry) {\n    synchronized(this) { entries += e }\n    auditLog.record(e)                   // 1. no Ledger lock held while calling out\n}\n\nfun flush() {\n    val b = ledger.balance()             // 2. read the balance before taking our own lock\n    val batch = synchronized(this) {\n        pending.toList().also { pending.clear() }\n    }\n    write(batch, b)                      // 3. slow file writing with no lock at all\n}", "alt_lang": "kotlin"},
   {"say": "Now no thread ever holds one of the two locks while asking for the other, so hold and wait is gone and no cycle can form. The balance written with the batch may be a moment older than the last entry. For an audit log that's fine. If it weren't, you'd need one lock over both, which is the one-lock design we started from.",
    "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Fix a transfer deadlock, then add a transfer that gives up",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/Transfers.java", f"{lab}/main/{P}/Account.java"],
  "run": "./gradlew :concurrency:test --tests 'workbench.concurrency.l06.*'",
  "steps": [
   "Run the tests. Two transfer tests time out after 10 seconds: they deadlocked. The three `tryTransfer` tests fail with `UnsupportedOperationException`.",
   "Read `Account`, a bank account with an id, a balance and its own `ReentrantLock`. You don't change it. `debit` (take money out) and `credit` (put money in) throw unless you hold that account's lock, so a forgotten lock fails loudly.",
   "Part 1: fix `Transfers.transfer` so it always locks the account with the lower `id()` first. Keep the `try`/`finally` around each `unlock()`.",
   "Part 2: write `tryTransfer`. Loop until the deadline: `tryLock` the first account for 10 ms, then the second for 10 ms. If you get both, move the money and return true. If not, release what you hold, sleep a random 1 to 10 ms, and loop. Return false when time is up.",
   "Run the tests until all five pass, then run them twice more."
  ],
  "hints": [
   "A transfer from an account to itself (`from == to`) takes the same `ReentrantLock` twice. That's fine, because it's reentrant, as long as you release it twice.",
   "In part 2, put the `from.lock().unlock()` in a `finally` that runs whether or not you got `to`. The test checks that `from` is free after a failed attempt.",
   "`ThreadLocalRandom.current().nextLong(1, 10)` gives a random back-off without sharing a `Random` between threads."
  ],
  "done_when": "All five tests in `TransfersTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Ordered locking from memory",
  "minutes": 4,
  "prompt": "Close this page. Write `transfer(Account from, Account to, long cents)` using each account's `ReentrantLock`, so that two transfers in opposite directions can never deadlock. Then check your work: does every `lock()` have its `unlock()` in a `finally`?",
  "answer": {"lang": "java", "src": J_DRILL, "alt": {"lang": "kotlin", "title": "Kotlin", "src": K_DRILL}}
 },
 "recap": [
  "A deadlock is a cycle of threads, each holding a lock the next one wants. Nothing throws: the threads sit BLOCKED, and the processor goes idle.",
  "Deadlock needs all four conditions: mutual exclusion, hold and wait, no preemption, circular wait. Break any one.",
  "The usual fix is a global lock order by a unique, stable key, written once in a helper and used everywhere.",
  "Timed `tryLock` with release and a random back-off means no wait lasts forever. Retrying in step gives livelock, and a lock that always lets the fast threads go first can starve a slow one.",
  "`jcmd <pid> Thread.print` (or `jstack`) names the threads and locks in a Java-level deadlock, on monitors and on `ReentrantLock`. Take it before you restart.",
  "The limit: the detector sees only Java locks, so a deadlock over pooled things such as database connections shows up only in the stacks, and `synchronized` can't time out. Timeouts need the explicit locks of the next lesson."
 ],
 "closing": "We started with a bank that gave each account its own lock and froze on a busy day without a word. We froze two transfers, asked the JVM what happened, found the four conditions behind it, and broke them twice: with one lock order, and with a lock that gives up.\n\nNow search your own code for a lock taken inside another: a nested `synchronized`, or `withLock` inside `withLock`. For each pair, ask what decides the order. If the answer is \"whichever argument comes first\", that pair can freeze just as Ana's and Ben's transfers did.\n\nNext, we'll look properly at the lock that gives up, `ReentrantLock`, and its partners `Condition` and `ReadWriteLock`. What can they do that `synchronized` can't, and what do they ask in return?",
 "quiz": [
  {"q": "Which change makes `transfer(from, to)` safe from deadlock when transfers run in both directions?",
   "options": ["Mark the field that holds each balance `volatile`", "Always lock the account with the lower id first, then the other", "Add `Thread.sleep(1)` between the two locks", "Make `transfer` a `synchronized` instance method on each account"],
   "answer": 1, "why": "One global order means no thread can hold the second lock while waiting for the first, so circular wait can't happen. `volatile` has nothing to do with locking, and a sleep only changes the odds. The tempting one is the `synchronized` method: on the source account it is still \"lock `from`, then `to`\", the same broken order."},
  {"q": "Two threads use `tryLock` with a fixed 5 ms sleep between attempts. A thread dump shows both RUNNABLE or TIMED_WAITING, their stacks change between dumps, and no deadlock is reported. Nothing has completed in a minute. What is this?",
   "options": ["A deadlock that the JVM failed to detect", "Starvation of one thread", "Livelock: they keep retrying in step and both keep failing", "A pause for garbage collection"],
   "answer": 2, "why": "The threads are active, they release and retake locks, and neither makes progress. That's livelock, and the fixed sleep keeps them in step; a random back-off breaks the symmetry. It isn't deadlock, because nobody waits forever on a held lock. It isn't starvation either, because starvation needs other threads that do make progress."},
  {"q": "A program stops answering. You suspect a lock cycle. Which tool tells you for sure?",
   "options": ["A JFR recording, filtered on the jdk.Deadlock event", "The garbage collector's log", "Restarting the program and watching whether it happens again", "`jcmd <pid> Thread.print`, which prints \"Found one Java-level deadlock\" with the threads and locks involved"],
   "answer": 3, "why": "The thread dump's deadlock detector finds cycles on monitors and on `ReentrantLock`, and names who holds what. JFR has no deadlock event, so the first option sounds right and finds nothing. Restarting destroys the evidence. Take the dump first."},
  {"q": "A report thread needs a `ReentrantLock` for 50 ms once a minute. Transfer threads take the same lock thousands of times a second and grab it again the moment they release it. The report sometimes waits for minutes. What is this, and what is one fix?",
   "options": ["Starvation; a fair lock, `new ReentrantLock(true)`, gives the longest waiter the next turn", "Deadlock; order the locks", "Livelock; add random back-off", "A race condition; make the field volatile"],
   "answer": 0, "why": "Everyone else makes progress and one thread never gets its turn: that's starvation. A non-fair lock lets a running thread take the lock again ahead of waiting threads. A fair lock serves them in order, at some cost in throughput. It isn't deadlock, because the lock keeps changing hands. Making the transfers hold the lock for less time also helps."},
  {"q": "From wait, notify and guarded blocks: the kitchen's rail with room for one ticket, using `notify()`, stalls with all four threads WAITING. Will `jcmd Thread.print` report a Java-level deadlock?",
   "options": ["Yes, every stall is reported as a deadlock", "No: no thread holds the monitor, they are all waiting for a notification that will never come", "Yes, but only with the -l flag", "No, because jcmd can't see WAITING threads"],
   "answer": 1, "why": "The deadlock detector looks for threads blocked on locks that the others hold. Threads in `wait()` hold nothing, and the monitor is free. They're stuck because a signal went to the wrong thread, not because of a lock cycle, so the dump shows four WAITING threads and no deadlock section. jcmd sees WAITING threads perfectly well; there's just no cycle to report.",
   "from": "conc-05"}
 ],
 "flashcards": [
  {"front": "Deadlock condition 1: what is mutual exclusion?", "back": "A resource can be held by only one thread at a time. Every lock has it."},
  {"front": "Deadlock condition 2: what is hold and wait?", "back": "A thread holds one resource while waiting for another."},
  {"front": "Deadlock condition 3: what is no preemption?", "back": "Nobody can take a resource away from the thread that holds it; only the holder can release it."},
  {"front": "Deadlock condition 4: what is circular wait?", "back": "A cycle of threads, each waiting for a resource the next one holds: T1 waits for T2, T2 waits for T1."},
  {"front": "How does a global lock order prevent deadlock?", "back": "Every thread takes locks in the same order (for example lower id first), so no cycle can form. It breaks circular wait."},
  {"front": "Deadlock vs livelock vs starvation, in one line each.", "back": "Deadlock: threads wait forever for each other. Livelock: threads stay busy reacting to each other and make no progress. Starvation: others progress, one thread never gets a turn."},
  {"front": "What does `jcmd <pid> Thread.print` print when it finds a lock cycle?", "back": "`Found one Java-level deadlock:`, then each thread, the lock it waits for and who holds it, then their stacks, ending with `Found 1 deadlock.`"}
 ],
 "terms": [
  {"term": "Deadlock", "plain": "Threads that each wait for a resource another one holds, so none can ever proceed."},
  {"term": "Livelock", "plain": "Threads that keep reacting to each other, busy but making no progress."},
  {"term": "Starvation", "plain": "One thread never gets the resource it needs while others keep getting it."},
  {"term": "Lock ordering", "plain": "A rule that every thread takes locks in the same global order."},
  {"term": "Wait-for graph", "plain": "A picture of which thread waits for which. A cycle in it is a deadlock."},
  {"term": "Thread dump", "plain": "A snapshot of every thread's state and stack, from `jcmd Thread.print` or `jstack`."},
  {"term": "Back-off", "plain": "A short pause, ideally of random length, before a thread tries again."},
  {"term": "Fair lock", "plain": "A lock that serves the longest-waiting thread first, so no thread starves, at some cost in speed."}
 ],
 "explain_back": {
  "prompt": "A friend says: \"We added `tryLock(5, SECONDS)` everywhere, so we can't have deadlocks any more.\" Explain what they got right, and what can still go wrong.",
  "answer": "They're right that a timed `tryLock` means no thread waits forever, so the classic deadlock can't freeze the program: a thread that can't get its second lock gives up after the timeout. But giving up only helps if the code then releases what it holds and tries again later, ideally after a random back-off. If two threads retry in step, they can livelock, failing over and over. A 5-second timeout also means a transfer can stall for 5 seconds before it even notices. Lock ordering removes the cycle altogether, so I'd use that where we can, and keep timed `tryLock` for the cases where we can't know the order up front."
 },
 "deeper": {
  "minutes": 10,
  "body": "The JVM's detector covers two kinds of lock. `ThreadMXBean.findDeadlockedThreads()` looks for cycles on monitors and on ownable synchronizers, locks that one thread owns, such as `ReentrantLock` and the write lock of `ReentrantReadWriteLock` (a lock with separate sides for readers and writers, from the next lesson). The older `findMonitorDeadlockedThreads()` sees monitors only. Neither sees semaphores and latches (the counters and one-time gates of lesson 10 of this track), `Object.wait()`, futures waiting on each other or pooled connections, because none of those has a single owning thread the JVM could point at.\n\nThat blind spot covers a common case: two thread pools waiting on each other. A thread pool is a fixed group of threads that runs the tasks you hand it, and a `Future` is a handle to a task's result that may not be ready yet. Task A runs on pool 1 and waits for a `Future` from pool 2, while pool 2's only thread waits for a `Future` from pool 1. No lock is involved, so the detector stays silent. The dump still gives it away if you read the stacks: every pool thread is parked in `FutureTask.get` or `CompletableFuture.join`. *Java Concurrency in Practice* calls this thread-starvation deadlock.\n\nFor tooling, `jcmd <pid> Thread.dump_to_file -format=json dump.json` writes the dump as JSON, and the format keeps improving. On JDK 21 each thread has only `tid`, `name` and `stack`. JDK 25 added per-thread `state`, `parkBlocker`, `blockedOn`, `waitingOn`, `owner` and the monitors each thread owns, which is enough to rebuild the wait-for graph. JDK 26 added `java.util.concurrent` lock information. JDK 27 added a `formatVersion` field. If you build tooling on these dumps, check that field and the JDK version first.\n\nTwo smaller notes. Ordering needs a unique key; with none, *Java Concurrency in Practice* breaks ties with `System.identityHashCode` and one extra global lock. And a fair `ReentrantLock` only orders the lock's own queue: its Javadoc warns that fairness of locks doesn't guarantee fairness of thread scheduling.\n\nDatabases take the opposite approach to the JVM. Oracle, for example, detects deadlocks between sessions (open connections to the database) and breaks them by failing one statement. Your code must be ready to retry that transaction, ideally after ordering its row locks so the retry doesn't deadlock again."
 },
 "sources": [
  {"title": "Deadlock (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/deadlock.html"},
  {"title": "Starvation and livelock (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/starvelive.html"},
  {"title": "ThreadMXBean (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.management/java/lang/management/ThreadMXBean.html"},
  {"title": "ReentrantLock.java at jdk-25-ga (tryLock and fairness notes)", "url": "https://github.com/openjdk/jdk/blob/jdk-25-ga/src/java.base/share/classes/java/util/concurrent/locks/ReentrantLock.java"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 10", "url": "https://jcip.net/"}
 ]
}
out = ROOT / "content/lessons/conc-06.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print(out)
