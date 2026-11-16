import json, pathlib
ROOT = pathlib.Path("/home/user/jvm-workbench")
lab = "labs/ledger/src"
P = "java/workbench/ledger/l01"
DJ = "java/workbench/ledger/l01/demo"
DK = "kotlin/workbench/ledger/l01/demo"
read = lambda p: (ROOT / p).read_text()
RUN = "./gradlew :ledger:demo -Pmain=workbench.ledger.l01.demo."


def demo(name, title_java=None):
    """A Java demo with its runnable Kotlin twin, both read from disk."""
    return {"lang": "java", "title": f"{name}.java", "src": read(f"{lab}/demo/{DJ}/{name}.java"),
            "run": RUN + name, "file": f"{lab}/demo/{DJ}/{name}.java",
            "alt": {"lang": "kotlin", "title": f"{name}.kt", "src": read(f"{lab}/demo/{DK}/{name}.kt"),
                    "run": RUN + name + "Kt", "file": f"{lab}/demo/{DK}/{name}.kt"}}


FIGURE = (
    '<svg viewBox="0 0 640 250" role="img" aria-label="Two opposite transfers between acc-03 and acc-07 both lock acc-03 first, '
    'so the second one waits while holding nothing">'
    '<text class="t-s t-m" x="160" y="24">time</text>'
    '<line class="ln-d" x1="200" y1="20" x2="630" y2="20" marker-end="url(#arr)"/>'
    '<text class="t" x="20" y="72">T1</text><text class="t-s t-m" x="20" y="90">acc-07 to acc-03</text>'
    '<rect class="box-a" x="160" y="56" width="105" height="36" rx="8"/><text class="t t-code" x="212" y="79" text-anchor="middle">lock 03</text>'
    '<rect class="box-a" x="285" y="56" width="105" height="36" rx="8"/><text class="t t-code" x="337" y="79" text-anchor="middle">lock 07</text>'
    '<rect class="box-ok" x="410" y="56" width="105" height="36" rx="8"/><text class="t" x="462" y="79" text-anchor="middle">check, move</text>'
    '<rect class="box" x="535" y="56" width="95" height="36" rx="8"/><text class="t" x="582" y="79" text-anchor="middle">release</text>'
    '<line class="ln" x1="265" y1="74" x2="283" y2="74" marker-end="url(#arr)"/>'
    '<line class="ln" x1="390" y1="74" x2="408" y2="74" marker-end="url(#arr)"/>'
    '<line class="ln" x1="515" y1="74" x2="533" y2="74" marker-end="url(#arr)"/>'
    '<text class="t" x="20" y="162">T2</text><text class="t-s t-m" x="20" y="180">acc-03 to acc-07</text>'
    '<rect class="box-dim" x="160" y="146" width="355" height="36" rx="8"/>'
    '<text class="t-s" x="337" y="169" text-anchor="middle">waits for 03, holding nothing</text>'
    '<rect class="box-a" x="535" y="146" width="95" height="36" rx="8"/><text class="t t-code" x="582" y="169" text-anchor="middle">lock 03</text>'
    '<line class="ln-d" x1="582" y1="92" x2="582" y2="144" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="337" y="222" text-anchor="middle">one order for both: a short wait, never a cycle</text>'
    '</svg>')

APPLY_JAVA = """public Outcome apply(Transfer t) {
    Account from = account(t.from()), to = account(t.to());
    Account first = from.id().compareTo(to.id()) < 0 ? from : to;   // 1. one order for everyone
    Account second = first == from ? to : from;
    first.lock().lock();
    try {
        second.lock().lock();
        try {
            if (from.balance() < t.cents()) return Outcome.INSUFFICIENT_FUNDS;   // 2. check...
            from.debit(t.cents());                                         // 3. ...and act
            to.credit(t.cents());
            return Outcome.APPLIED;
        } finally {
            second.lock().unlock();
        }
    } finally {
        first.lock().unlock();                                             // 4. on every path
    }
}"""

APPLY_KT = """fun apply(t: Transfer): Outcome {
    val from = account(t.from); val to = account(t.to)
    val first = if (from.id < to.id) from else to                      // 1. one order for everyone
    val second = if (first === from) to else from
    return first.lock.withLock {
        second.lock.withLock {
            if (from.balance < t.cents) return Outcome.INSUFFICIENT_FUNDS  // 2. check...
            from.debit(t.cents)                                            // 3. ...and act
            to.credit(t.cents)
            Outcome.APPLIED
        }
    }                                                                      // 4. withLock releases in a finally
}"""

L = {
 "id": "cap1-01",
 "title": "Design the ledger and make it correct",
 "minutes": 40,
 "goal": "By the end you can write down a ledger's rules before its code, protect them with one lock per account taken in one fixed order, model a transfer as a value that can't change, and test every rule with 8 threads making 100,000 transfers each.",
 "opening": """Picture a small bank with 50 accounts. It keeps a ledger: the bank's book of accounts, with every movement of money between them. A transfer takes money out of one account and puts the same amount into another, say 20.00 from Ana to Ben. All day, customers send each other money, and many transfers arrive at the same moment.

Part 1 has visited this bank before, one bug at a time. Deposits went missing in a race. Ana and Ben paid each other at once, and the program froze. Now we build the whole ledger, in three sittings.

The easy trap is to write the transfer first and decide what "correct" means later. On one thread, one path of work through the program, a transfer can't go wrong. On eight threads, the bank creates money and destroys it again, by millions of cents, and nothing ever throws.

The last lesson, Moving a blocking service to virtual threads, closed the virtual threads track. In this lesson, we'll write the ledger's rules down first. Then we'll make a transfer that can't change, give each account its own lock, and build a test that tries hard to break it all. Before we start, make a guess, and keep it in mind.""",
 "warmup": {
  "q": "Our bank has 50 accounts holding 500,000 cents in total. Eight threads each make 100,000 random transfers with `if (balance[from] >= c) { balance[from] -= c; balance[to] += c; }` on a plain `long[]`, with no locks. What is the total at the end?",
  "options": ["Exactly 500,000, because every transfer adds what it subtracts",
              "Some other number, different on every run",
              "Exactly 500,000, but some balances are negative",
              "The JVM throws a ConcurrentModificationException"],
  "answer": 1,
  "why": "Each `-=` and `+=` is three steps: read the balance, change it, write it back. When two threads change the same account at the same moment, one of the two changes is lost. A lost debit creates money and a lost credit destroys it, so the total drifts, often by millions of cents. Nothing throws, because a plain array checks nothing. `ConcurrentModificationException` comes from collections such as `ArrayList`, and only when they notice a change in the middle of a loop."
 },
 "sections": [
  {
   "h": "Three rules before any code: what a correct ledger must keep",
   "body": """Over three sittings, we'll build the ledger from the inside out. This sitting builds the core: accounts, locks, transfers and a test. The next one runs the ledger on a thread pool, a small team of threads that takes tasks from a queue. The last one serves thousands of customers at once on virtual threads, threads so light that a program can run thousands of them. Each piece comes from an earlier lesson, and we'll name that lesson when we lean on it.

The core starts with the smallest ledger that can be wrong. It keeps 50 balances in an array, in cents, and has no locks at all. A thread, one path of work running beside others in the same program, calls `transfer` to move money:

```java
long[] balance = new long[50];          // 10,000 cents each, 500,000 in total

void transfer(int from, int to, long cents) {
    if (balance[from] >= cents) {       // check
        balance[from] -= cents;         // read, subtract, write
        balance[to] += cents;           // read, add, write
    }
}
```

```kotlin
val balance = LongArray(50) { 10_000L } // 500,000 cents in total

fun transfer(from: Int, to: Int, cents: Long) {
    if (balance[from] >= cents) {       // check
        balance[from] -= cents          // read, subtract, write
        balance[to] += cents            // read, add, write
    }
}
```

Every transfer takes out what it puts in, so the total should stay at 500,000 cents forever. Let's run eight threads that each make 100,000 random transfers. One run on the busy machine used for this course printed:

```text
run 1: total 1,306,080 cents, expected 500,000, off by 806,080
run 2: total 4,043,302 cents, expected 500,000, off by 3,543,302
run 3: total 4,941,343 cents, expected 500,000, off by 4,441,343
```

By the third run, the bank holds ten times the money its customers ever paid in. Generous, and very wrong.

Race conditions: why count++ lies showed the cause. `balance[from] -= cents` is three steps: read the balance, subtract, write it back. Say account 3 holds 100. Thread 1 reads 100 to send 20, and at the same moment thread 2 reads 100 to send 30. Thread 1 writes 80. Thread 2 writes 70. Both transfers paid out, but only one debit stuck, so 20 cents now exist twice. That is a **lost update**, and a lost credit destroys money the same way.

Before we fix it, let's decide what fixed means. An **invariant** is a rule about the data that must be true whenever another thread can look. Our ledger has three:

1. Money is conserved: the sum of all balances never changes.
2. No balance ever goes below zero.
3. A transfer happens whole or not at all: nobody sees the debit without the credit.

Each rule decides part of the design. Rules 1 and 3 say the debit and the credit must be one step that no other thread can split, and that step touches two accounts. Rule 2 says the balance check belongs inside that same step. A check in one step and a debit in another is **check-then-act**, the second shape of race from Race conditions. Another thread can act in the gap between the two. And "whenever another thread can look" tells us when to test: while the threads run, not only at the end.

**A ledger is correct only against rules you can name. Write them down before the code.**

The rest of this lesson builds the ledger so that every line points at one of these three rules. We'll start with the thing that moves between threads: the transfer itself.""",
   "try": {
    "title": "Count what a ledger without locks loses",
    "minutes": 3,
    "steps": [
     "Open `BrokenLedgerDemo` (or its Kotlin twin). Before you run it, write down the total you expect after each run.",
     "Run it with the command below. Note how far off each run is, and in which direction.",
     "Run it again with `-Pargs=1000`, so each thread makes only 1,000 transfers. The threads still wait at a start line and leave together. Predict first: will the total be right now?"
    ],
    "code": demo("BrokenLedgerDemo"),
    "expect": "With 100,000 transfers per thread, the total is off by hundreds of thousands or millions of cents, by a different amount every run (from 300,421 to 4,848,480 cents in Java and Kotlin runs here). Once, while the machine was very busy, two runs out of three came out exactly right. That is the most dangerous result of all, because a correct run proves nothing. With 1,000 transfers per thread, most runs are still wrong, by thousands of cents, because the start line releases all eight threads at the same moment. Without a start line, short runs often look correct, because each thread finishes before the next one starts."
   }
  },
  {
   "h": "A transfer travels between threads, so make it a value that can't change",
   "body": """A transfer is built in one place and used in others. Say the bank imports a file of transfers each night. One thread reads the file line by line, and a thread pool applies each line to the ledger. Later, a log line prints the same transfer. If anyone can change the transfer after it is built, the others can see two different versions of it.

Here is the most common way that goes wrong. The importer reuses one row object for every line, to save memory, and hands the row to the pool:

```java
TransferRow row = new TransferRow();             // changeable, and reused for every line
for (String line : file) {
    row.parse(line);                             // overwrites id, from, to, cents
    pool.execute(() -> ledger.apply(row));       // a pool thread reads row later
}
```

```kotlin
val row = TransferRow()                          // changeable, and reused for every line
for (line in file) {
    row.parse(line)                              // overwrites id, from, to, cents
    pool.execute { ledger.apply(row) }           // a pool thread reads row later
}
```

By the time a pool thread reads `row`, the importer has moved on to later lines. This section's demo imports 100,000 lines this way. One run printed:

```text
file: 100,000 lines, 54,910,000 cents
applied: 13,920 different lines, 48,394,607 cents, 40 rows mixing two lines
```

The ledger applied 100,000 transfers built from only 13,920 different lines. Forty rows carried the id of one line and the amount of another. In another run, only 15 different lines arrived at all. The bank paid a handful of customers thousands of times and most of them never.

Happens-before, the rules that matter, named the cause. **Happens-before** is the memory model's promise that one thread sees what another wrote before a handover. That lesson pictured the handover as a cashier who locks the cabinet and leaves the key for the night manager. Handing a task to a pool is such a handover, but it covers only what was written before `execute`. The importer's later writes to the same row have no handover at all. That's a **data race**: two threads use the same field, at least one of them writes, and no happens-before rule links them. The reader can see any mix of old and new values.

The fix is a value that can't change once it's built. A Java record, or a Kotlin `data class` with only `val` properties, has final fields and no setters:

```java
public record Transfer(String id, String from, String to, long cents) {
    public Transfer {                            // compact constructor: runs before the fields are set
        Objects.requireNonNull(id, "id");
        Objects.requireNonNull(from, "from");
        Objects.requireNonNull(to, "to");
        if (cents <= 0) throw new IllegalArgumentException("amount must be positive");
        if (from.equals(to)) throw new IllegalArgumentException("two different accounts");
    }
}
```

```kotlin
data class Transfer(val id: String, val from: String, val to: String, val cents: Long) {
    init {                                       // runs on every construction, copy() included
        require(cents > 0) { "amount must be positive" }
        require(from != to) { "two different accounts" }
    }
}
```

The Java version uses a **compact constructor**, a record constructor without a parameter list. It runs before the fields are set, so it can refuse bad values. Kotlin's `init` block does the same job, and Kotlin's non-null types make the three null checks unnecessary.

Two things come with this design. First, Safe publication, final fields and escaping this compared an object with final fields to a letter in a sealed envelope. Any thread that receives it reads every page, however it got there. Second, the checks run once, when the transfer is built, so a `Transfer` that exists is a valid one. The ledger never asks whether `cents` is negative or whether `from` equals `to`, and the lock order in the next section relies on two different accounts.

One more choice hides in that record: money is a `long` count of cents. A `double` can't hold 0.10 exactly. Add 0.10 and 0.20 as doubles and Java prints `0.30000000000000004`, so a ledger of doubles drifts away from rule 1 with no thread involved.

**A value that crosses threads should never change. Make it a record, and check it in the constructor.**

The transfer is now safe to hand to any thread. The accounts it touches are not, and two transfers can touch the same account at the same moment.""",
   "try": {
    "title": "Reuse one row, then use a record",
    "minutes": 3,
    "steps": [
     "Run `ReusedTransferDemo`. It reads 100,000 lines and hands each one to a pool of 4 threads. Predict first: how many different lines reach the ledger?",
     "Run it again with `-Pargs=record`, which builds a new `Transfer` record for each line."
    ],
    "code": demo("ReusedTransferDemo"),
    "expect": "With the reused row, only some of the lines arrive (from 15 to 24,580 different lines in Java and Kotlin runs here), the cents never match the file, and up to about a thousand rows mix one line's id with another line's amount. With a record, all 100,000 lines arrive, the cents match the file and nothing is mixed. Each record is built once, handed to the pool (a happens-before handover), and never written again."
   },
   "refs": [
    {"title": "Java Language Specification, section 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10", "kind": "docs"}
   ]
  },
  {
   "h": "One lock per account, always taken in the same order",
   "body": """Rules 1 and 3 need the debit and the credit to happen as one step. Synchronized and intrinsic locks gave us the tool. A **lock** lets one thread at a time into a piece of code, and that lesson pictured it as the key to the bank's vault. A thread takes the key, goes in, changes the balances and hands the key on. Everyone else waits at the door. The code a thread runs while it holds the key is the **critical section**.

The simplest design is one key for the whole ledger. It is correct, and it keeps all three rules. Its cost is that every transfer waits for every other one, even a transfer between two strangers that shares no account with yours. So we give each account its own key. Then a transfer between accounts 3 and 7 and another between 12 and 40 can run at the same time.

Two keys per transfer bring back the freeze from Deadlock, livelock and starvation. Ana sends Ben 100 at the same moment Ben sends Ana 50. Ana's transfer takes her key and waits for Ben's. Ben's transfer takes his key and waits for Ana's. Each waits forever for the other: that's a **deadlock**. The fix from that lesson works here as it is. Give every account a unique id that never changes, and always lock the smaller id first, whichever way the money moves:

```java
""" + APPLY_JAVA + """
```

```kotlin
""" + APPLY_KT + """
```

Let's read it in order. First we look up both accounts and decide which one comes first by id (1). Then we take the two locks in that order. Under both locks we check the balance (2), and only then debit and credit (3). Finally, the `finally` blocks give both locks back on every path (4), including the early return for a refusal.

Each line traces back to a rule. Follow the figure below. A transfer from acc-07 to acc-03 and one from acc-03 to acc-07 start at the same moment, and both ask for acc-03 first. One gets it. The other waits for acc-03 while holding nothing, so nobody can be waiting for it, and no cycle can form. A transfer between acc-12 and acc-40 that comes along later needs neither key, and runs straight through. The check sits under both locks, so no other transfer can spend the same money between the check and the debit. And a thread that takes both locks never sees half a transfer.

The id is a `String`, compared with `compareTo`. It's unique and never changes, and that's all an order needs. `hashCode()` would not do: two accounts can share a hash code, and then two threads can disagree about which one comes first.

Why `ReentrantLock`, the lock object from the lesson on explicit locks, and not `synchronized`? For today's code they behave the same. The choice pays off in lesson 3 of this track, where thousands of virtual threads wait for these locks. On JDK 21, a virtual thread waiting at a `synchronized` block can't let go of the thread that carries it. Keep that promise in mind; we'll come back to it.

The lab's `Account` class is strict about its key. Call `debit` without holding the account's lock, and it refuses at once: `take the lock of account acc-03 first`. A missing lock fails loudly in a test, instead of losing money quietly later.

What do the extra keys buy? This section's demo counts how many transfers are inside a critical section at once, then times both designs. One run printed:

```text
8 threads x 50,000 transfers, 50 accounts, 50 steps of work inside the lock
one ledger lock     294 ms, total 500,000, most transfers in progress at once: 1
per-account locks   336 ms, total 500,000, most transfers in progress at once: 4
```

The count did what we expected: one at a time with one lock, and about as many as the machine's four cores with a lock per account. The time did not. On this busy machine, the per-account version was no faster. With no work inside the lock, the single lock was often a little quicker, because handing a lock from thread to thread costs more than the few instructions it guards. Both kept the total at 500,000. Count first, then measure, and only then argue.

**Every path that takes two locks must take them in one order. Lower id first, always.**

The design is done, and it looks right. But code that looked right has fooled us all through Part 1, so the last step is a test that tries hard to break it.""",
   "figure": {"svg": FIGURE, "caption": "T1 and T2 move money in opposite directions, and both lock acc-03 first. T2 waits for that lock while holding nothing, so no cycle can form."},
   "aside": {
    "title": "Doesn't a database do this for me?",
    "body": "If your ledger lives in a database, a program that keeps data on disk and answers queries, it offers the same ideas under other names. A query such as `SELECT ... FOR UPDATE` locks the rows it reads, which is the database's way of taking an account's key. Two transactions, groups of changes the database applies as one, that lock the same two rows in opposite orders deadlock just like Ana and Ben, and the database then cancels one of them with an error. The fix is the same: lock the rows sorted by account id. A rule such as `CHECK (balance >= 0)` on the table refuses any change that takes a balance below zero, which is rule 2 written where nobody can skip it."
   },
   "try": {
    "title": "Count the transfers in progress",
    "minutes": 4,
    "steps": [
     "Run `LockGranularityDemo`. It runs the same 400,000 random transfers under one ledger-wide lock, then under one lock per account, taken in id order. Each transfer does 50 small steps of work inside its locks.",
     "Before you read the output, predict the last column, \"most transfers in progress at once\", for each design.",
     "Run it with `-Pargs=0` (no work inside the lock) and with `-Pargs=200`. Compare the times, and explain any surprise."
    ],
    "code": demo("LockGranularityDemo"),
    "expect": "With one lock, the last column is always 1. With a lock per account, it shows about as many as your cores (2 to 5 on the 4-core machine used here; a thread that the operating system pauses inside a lock still counts). The times depend on your machine and on what else it is doing. On this busy machine, the per-account version took 277 to 336 ms against 276 to 294 ms for one lock, with `-Pargs=0` the single lock was a little faster, and with `-Pargs=200` the two came out about even. More work inside the lock gives the extra locks more to overlap, so they help most when cores are free. The total is 500,000 in every row: both designs keep the rules."
   },
   "refs": [
    {"title": "ReentrantLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html", "kind": "docs"}
   ]
  },
  {
   "h": "A stress test that makes threads collide and checks every rule",
   "body": """A **stress test** runs many threads and many operations at once, on purpose, to make bugs show. Testing and debugging concurrent code told the story of a refund test whose two threads never met. On a quiet machine, the first one finished before the second one started. That lesson's habits fix it: a start line so the threads overlap, more threads than cores, many operations, and checks after every thread has finished.

The start line is a **latch**, a counter that threads can wait on. When it reaches zero, every waiting thread goes at once, like runners at the starting gun in Synchronizers. The lab's harness runs 8 threads that each make 100,000 random transfers between 50 accounts:

```java
CountDownLatch ready = new CountDownLatch(threads), go = new CountDownLatch(1);
List<Thread> workers = new ArrayList<>();
for (int i = 0; i < threads; i++) {
    int me = i;
    workers.add(Thread.ofPlatform().start(() -> {
        ready.countDown();
        try { go.await(); } catch (InterruptedException e) { return; }   // the start line
        long ok = 0, no = 0;                       // counted in locals: nothing shared
        for (int n = 0; n < perThread; n++) {
            if (ledger.apply(randomTransfer(me, n)) == APPLIED) ok++; else no++;
        }
        applied[me] = ok; refused[me] = no;        // one slot per thread
    }));
}
ready.await(); go.countDown();                     // release them together...
for (Thread w : workers) w.join();                 // ...and wait for all of them
```

```kotlin
val ready = CountDownLatch(threads); val go = CountDownLatch(1)
val workers = List(threads) { me ->
    thread {
        ready.countDown()
        go.await()                                 // the start line
        var ok = 0L; var no = 0L                   // counted in locals: nothing shared
        repeat(perThread) { n ->
            if (ledger.apply(randomTransfer(me, n)) == APPLIED) ok++ else no++
        }
        applied[me] = ok; refused[me] = no         // one slot per thread
    }
}
ready.await(); go.countDown()                      // release them together...
workers.forEach { it.join() }                      // ...and wait for all of them
```

Let's walk through it. Each worker counts down `ready`, then waits at `go`. The main thread waits until every worker is ready, then counts down `go`, which releases them all together. Each worker counts its own results in local variables, so nothing is shared while it runs, and it writes them into its own slot at the end. Finally, `join()` waits for every worker, and it is also a handover: after it, the main thread sees every slot.

After the joins, the test checks four things. The total is still 500,000. No balance is negative. Applied plus refused is 800,000, so no transfer vanished. And some transfers were refused, which proves the overdraft branch ran at all.

That list has a hole, and this section's demo falls right into it. Take a ledger that locks in id order, but checks the balance before it takes the locks. Here is one run:

```text
check, then lock and move
  total 500,000 (conserved), negative at the end: 0, overdrafts while running: 2,129
lock, then check and move
  total 500,000 (conserved), negative at the end: 0, overdrafts while running: 0
```

Money was conserved, because each move was still one step under both locks. No balance was negative at the end. Yet while it ran, 2,129 debits took an account below zero. Later credits topped those accounts up before anyone looked. A test that checks only the final state sees a healthy ledger.

So check each rule where it can break, as well as at the end. The lab's `Account.debit` throws `IllegalStateException` when a debit would overdraw, so a race that overdraws fails the stress test at once. The check costs one comparison, and in a real bank it turns a silent loss into an error someone sees.

**A rule checked only at the end can heal before you look. Check it where it can break.**

Then remember what a pass means. Eight threads and 800,000 transfers that find nothing make the ledger more believable. They don't prove it. The proof is the argument you can make for each rule from the code, which is why we wrote the rules down first.

That argument has an edge, too. Today's ledger runs on whatever threads happen to call it, and nothing decides how many there are. A bank with real customers has to choose its threads, and stop them at night without dropping a transfer. That's the next sitting.""",
   "try": {
    "title": "Find the bug that keeps the total right",
    "minutes": 4,
    "steps": [
     "Read `CheckOutsideLockDemo`. Both ledgers lock accounts in id order. The first checks the balance, looks up a fee, then takes the locks and moves the money. The second takes the locks first, then checks.",
     "Predict which rules each version breaks, then run it.",
     "Find the line that counts overdrafts. Explain why the \"negative at the end\" column misses what it counts."
    ],
    "code": demo("CheckOutsideLockDemo"),
    "expect": "Both totals are 500,000, and neither ledger ends with a negative balance. The first one still overdrew accounts while it ran (758 to 2,129 times in Java runs here, 1,298 in a Kotlin run); the second never did. Each move was one step under both locks, so rule 1 held. Rule 2 broke in the gap between the check and the locks, and later credits hid the evidence before the end."
   },
   "refs": [
    {"title": "CountDownLatch (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CountDownLatch.html", "kind": "docs"}
   ]
  }
 ],
 "compare": {
  "title": "The ledger's apply in Java and Kotlin",
  "java": {"title": "Ledger.java", "src": """public Outcome apply(Transfer t) {
    Account from = account(t.from());
    Account to = account(t.to());
    Account first = from.id().compareTo(to.id()) < 0 ? from : to;
    Account second = first == from ? to : from;
    first.lock().lock();
    try {
        second.lock().lock();
        try {
            if (from.balance() < t.cents()) return Outcome.INSUFFICIENT_FUNDS;
            from.debit(t.cents());
            to.credit(t.cents());
            return Outcome.APPLIED;
        } finally {
            second.lock().unlock();
        }
    } finally {
        first.lock().unlock();
    }
}"""},
  "kotlin": {"title": "Ledger.kt", "src": """fun apply(t: Transfer): Outcome {
    val from = account(t.from)
    val to = account(t.to)
    val first = if (from.id < to.id) from else to
    val second = if (first === from) to else from
    return first.lock.withLock {
        second.lock.withLock {
            if (from.balance < t.cents) return Outcome.INSUFFICIENT_FUNDS
            from.debit(t.cents)
            to.credit(t.cents)
            Outcome.APPLIED
        }
    }
}"""},
  "note": "Both versions take the same two locks in the same order; Kotlin just writes the `try`/`finally` for you. Its `withLock` is an inline function that calls `lock()`, runs the block and calls `unlock()` in a `finally`, so the two nested `try`/`finally` blocks become two nested blocks. Because `withLock` is inline, `return Outcome.INSUFFICIENT_FUNDS` inside it returns from `apply` itself, and both locks are still released. `from.id < to.id` on strings calls the same `compareTo` as the Java version. The `Transfer` differs only in style: a Kotlin `data class` of `val`s is exactly as shallow as a Java record. Both make the fields final, and neither copies a changeable list you pass in."
 },
 "worked": {
  "title": "Add a fee without breaking the rules",
  "steps": [
   {"say": "The bank decides to charge a small fee on each transfer, paid into a fee account the bank owns. Money is still conserved: the sender pays `cents + fee`, the receiver gets `cents` and the fee account gets `fee`. Now three accounts change in one step. Here is a first attempt. Read it against the three rules and the lock order before you go on.",
    "code": """Outcome applyWithFee(Transfer t, long fee) {
    Account from = account(t.from()), to = account(t.to());
    from.lock().lock();
    to.lock().lock();
    feeAccount.lock().lock();
    try {
        if (from.balance() < t.cents()) return Outcome.INSUFFICIENT_FUNDS;
        from.debit(t.cents() + fee);
        to.credit(t.cents());
        feeAccount.credit(fee);
        return Outcome.APPLIED;
    } finally {
        feeAccount.lock().unlock();
        to.lock().unlock();
        from.lock().unlock();
    }
}""", "lang": "java", "alt_lang": "kotlin",
    "alt_code": """fun applyWithFee(t: Transfer, fee: Long): Outcome {
    val from = account(t.from); val to = account(t.to)
    from.lock.lock()
    to.lock.lock()
    feeAccount.lock.lock()
    try {
        if (from.balance < t.cents) return Outcome.INSUFFICIENT_FUNDS
        from.debit(t.cents + fee)
        to.credit(t.cents)
        feeAccount.credit(fee)
        return Outcome.APPLIED
    } finally {
        feeAccount.lock.unlock()
        to.lock.unlock()
        from.lock.unlock()
    }
}"""},
   {"say": "There are two bugs. First, the locks are taken by role, sender first, not by id. A transfer from acc-02 to acc-05 locks 02, then 05, while a transfer from acc-05 to acc-02 locks 05, then 02. That's Ana and Ben again. Second, the check tests `cents`, but the debit takes `cents + fee`, so a sender with exactly `cents` left goes below zero. The lab's `debit` would throw; a plain field would go negative without a word.", "code": "", "lang": ""},
   {"say": "Sort every account the operation touches by id, lock them in that order, and release them in reverse. The same code works for two accounts, three, or a batch of fifty. `distinct()` covers the case where the sender is the fee account itself, because a `ReentrantLock` taken twice must also be released twice.",
    "code": """Outcome applyWithFee(Transfer t, long fee) {
    Account from = account(t.from()), to = account(t.to());
    List<Account> touched = Stream.of(from, to, feeAccount)
            .distinct()
            .sorted(Comparator.comparing(Account::id))      // 1. one global order, any number of locks
            .toList();
    touched.forEach(a -> a.lock().lock());
    try {
        if (from.balance() < t.cents() + fee) return Outcome.INSUFFICIENT_FUNDS;   // 2. check what is debited
        from.debit(t.cents() + fee);                         // 3. three changes, one critical section
        to.credit(t.cents());
        feeAccount.credit(fee);
        return Outcome.APPLIED;
    } finally {
        for (int i = touched.size() - 1; i >= 0; i--) touched.get(i).lock().unlock();   // 4. reverse order
    }
}""", "lang": "java", "alt_lang": "kotlin",
    "alt_code": """fun applyWithFee(t: Transfer, fee: Long): Outcome {
    val from = account(t.from); val to = account(t.to)
    val touched = listOf(from, to, feeAccount)
        .distinct()
        .sortedBy { it.id }                                  // 1. one global order, any number of locks
    touched.forEach { it.lock.lock() }
    try {
        if (from.balance < t.cents + fee) return Outcome.INSUFFICIENT_FUNDS   // 2. check what is debited
        from.debit(t.cents + fee)                            // 3. three changes, one critical section
        to.credit(t.cents)
        feeAccount.credit(fee)
        return Outcome.APPLIED
    } finally {
        touched.asReversed().forEach { it.lock.unlock() }    // 4. reverse order
    }
}"""},
   {"say": "Check it against the rules. Conservation: the sender loses `cents + fee`, and the other two gain exactly that. No overdraft: the check and the debit use the same amount, under the same locks. Whole or nothing: all three changes happen inside one set of locks. No deadlock: plain `apply` locks two accounts in id order and this method locks three in id order, so any two operations agree on which lock comes first. Where the fee account's id sorts among the customers' ids doesn't matter. Only the rule matters.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build the ledger and the test that tries to break it",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/Transfer.java", f"{lab}/main/{P}/Ledger.java", f"{lab}/main/{P}/StressHarness.java", f"{lab}/main/{P}/Account.java"],
  "run": "./gradlew :ledger:test --tests 'workbench.ledger.l01.*'",
  "steps": [
   "Run the tests once. All nine fail. Then read `Account`. You won't change it, but notice how strict it is: `debit` and `credit` throw unless you hold that account's lock, and `debit` throws on an overdraft.",
   "In `Transfer`, add the compact constructor from the section on transfers, so every `Transfer` that exists is valid: `Objects.requireNonNull` for `id`, `from` and `to`, and an `IllegalArgumentException` when `cents <= 0` or `from.equals(to)`.",
   "Write `Ledger.apply` with the lock order from Deadlock, livelock and starvation: look up both accounts, pick `first` and `second` with `id().compareTo`, lock them in that order with nested `try`/`finally`, then check the balance and move the money while you hold both locks.",
   "Write `StressHarness.run` with the start line from Synchronizers: a `ready` latch and a `go` latch, `threads` workers that each make `perThread` random transfers with `ThreadLocalRandom`, per-thread counts stored in a `long[]` slot at the end, then `join()` every worker and add up the slots.",
   "Run the tests until all nine pass. Then break `apply` on purpose: lock `from` first and `to` second, and watch the deadlock test fail after its 15 second limit. Put the order back."
  ],
  "hints": [
   "Two different random accounts without a retry loop: `int a = rnd.nextInt(n); int b = rnd.nextInt(n - 1); if (b >= a) b++;`.",
   "Build each transfer's id from the thread number and the loop counter, such as `\"t\" + me + \"-\" + n`. The test checks that no id repeats.",
   "Call `ThreadLocalRandom.current()` inside the worker's lambda, not before it. Each thread needs its own generator.",
   "If the overlap test fails, check that each worker counts down `ready` before it waits on `go`, and that `run` waits on `ready` before it counts down `go`."
  ],
  "done_when": "All nine tests in `LedgerTest` pass, three runs in a row."
 },
 "drill": {
  "title": "Write the ordered two-lock transfer from memory",
  "minutes": 5,
  "prompt": "Close the lab. In a blank file, write `Outcome move(Account from, Account to, long cents)` for accounts that have a unique `id()` and a `ReentrantLock lock()`. It must never deadlock, never overdraw and always release both locks. Then compare with the answer. Is your balance check inside both locks?",
  "answer": {"lang": "java", "src": """Outcome move(Account from, Account to, long cents) {
    Account first = from.id().compareTo(to.id()) < 0 ? from : to;   // lower id first, always
    Account second = first == from ? to : from;
    first.lock().lock();
    try {
        second.lock().lock();
        try {
            if (from.balance() < cents) return Outcome.INSUFFICIENT_FUNDS;   // check under both locks
            from.debit(cents);
            to.credit(cents);
            return Outcome.APPLIED;
        } finally {
            second.lock().unlock();
        }
    } finally {
        first.lock().unlock();
    }
}""",
   "alt": {"lang": "kotlin", "src": """fun move(from: Account, to: Account, cents: Long): Outcome {
    val first = if (from.id < to.id) from else to                   // lower id first, always
    val second = if (first === from) to else from
    return first.lock.withLock {
        second.lock.withLock {
            if (from.balance < cents) return Outcome.INSUFFICIENT_FUNDS     // check under both locks
            from.debit(cents)
            to.credit(cents)
            Outcome.APPLIED
        }
    }
}"""}}
 },
 "recap": [
  "Write the rules first: money is conserved, no balance goes below zero, a transfer is whole or not at all. Every line of `apply` protects one of them.",
  "Debit and credit happen in one critical section that holds both accounts' locks, and the balance check sits inside it too. A check outside the locks is check-then-act.",
  "Lock accounts in one global order, by a unique id that never changes (`compareTo`, never `hashCode`). For more than two accounts, sort them all, lock in order, release in reverse.",
  "A transfer is a value that can't change, checked in its constructor: safe to hand to any thread, and never invalid. A reused, changeable row handed to a pool delivers the wrong data.",
  "A stress test needs a start line, more threads than cores, many operations, and checks of every rule, at the end and where each one can break. A pass is evidence, not proof.",
  "Where today's ledger stops: it runs on whatever threads call it. Nothing yet decides how many threads there are, or how to stop them without dropping a transfer."
 ],
 "closing": """We started with a bank that created money and destroyed it again, without a single error. Now the ledger keeps its three rules on purpose: a sealed transfer, a key per account, one order for taking keys, and a test that checks each rule where it can break.

Now look in your own code for one lock taken inside another. For each pair, ask what decides the order. If the answer is "whichever argument comes first", that pair can freeze the way Ana and Ben did.

Next, we'll run the ledger on a pool of threads we size ourselves. How many threads does a busy bank need, and what happens to the transfers still waiting at closing time?""",
 "quiz": [
  {"q": "A teammate orders the two locks in `apply` by `System.identityHashCode(account)` instead of by account id. What can go wrong?",
   "options": ["Nothing: every object has a different identity hash code",
               "Two accounts can share a hash code, and then two transfers may lock them in opposite orders and deadlock",
               "The hash code changes when the garbage collector moves the object, so the order changes",
               "Nothing serious: ReentrantLock notices the deadlock and throws"],
   "answer": 1,
   "why": "Identity hash codes are not unique. When two accounts tie, neither one sorts first, so one thread may lock A first and another B first, which is the cycle Ana and Ben fell into. Java Concurrency in Practice breaks the tie with one extra lock; a unique account id avoids the problem. An identity hash code stays the same for the object's whole life, even when the garbage collector moves it, and no lock notices a deadlock for you.",
   "from": "conc-06"},
  {"q": "This `apply` locks both accounts in id order, but first it calls `if (balanceOf(from) < cents) return INSUFFICIENT_FUNDS;`, which takes and releases `from`'s lock. Eight threads stress it. Which rule can break?",
   "options": ["A balance can go below zero",
               "Money is no longer conserved",
               "Two opposite transfers can deadlock",
               "None: every step holds a lock"],
   "answer": 0,
   "why": "It's check-then-act: another transfer can spend the money between `balanceOf` and the locks. Each move is still one step under both locks, so the total is conserved, which is exactly why a test that only checks totals passes. Locks taken in id order can't deadlock. \"Every step holds a lock\" is the trap: two locked steps in a row are not one locked step.",
   "from": "conc-03"},
  {"q": "`record Transfer(String id, List<String> tags, long cents)`. The importer fills an `ArrayList` of tags, builds the record, hands it to a pool, then clears the list and reuses it for the next line. What can the pool thread see in `tags()`?",
   "options": ["The original tags, because records can't change",
               "A copy, because records copy their components",
               "An empty or half-changed list, because the record holds the importer's own list",
               "Nothing: `clear()` throws UnsupportedOperationException"],
   "answer": 2,
   "why": "A record is only shallowly immutable. Its field can't point at another list, but the list itself is still the importer's `ArrayList`, and clearing it changes what the pool thread reads. Copy it in the compact constructor with `tags = List.copyOf(tags)`, which also gives the record a list nobody can change. Records never copy their components for you.",
   "from": "conc-11"},
  {"q": "The ledger's stress test passed 50 runs in a row on your laptop. What have you shown?",
   "options": ["The ledger is thread-safe",
               "The ledger is thread-safe on Intel and AMD processors, but maybe not on ARM",
               "The JIT compiled the race away",
               "These runs found no failure; the argument that each rule holds has to come from the code"],
   "answer": 3,
   "why": "A stress test can show that a race exists, never that none does. Fifty clean runs with a start line and many threads make a bug less likely. The proof is the reasoning: which lock guards which field, and why each rule holds inside the critical section.",
   "from": "conc-13"},
  {"q": "Which change to the ledger breaks rule 3, \"a transfer happens whole or not at all\"?",
   "options": ["Locking `to` first whenever `to` has the lower id",
               "Replacing the `ReentrantLock`s with `synchronized` blocks taken in the same order",
               "Debiting inside one locked block, releasing both locks, then crediting inside a second locked block",
               "Making `Transfer` a Kotlin data class instead of a Java record"],
   "answer": 2,
   "why": "Between the two blocks, a thread that locks both accounts (a snapshot, an audit) sees the money gone from one account and not yet in the other, and an exception at that point loses it for good. The other changes keep debit and credit in one critical section: locking the lower id first is the rule itself, `synchronized` gives the same one-at-a-time access, and a data class can't change any more than a record can."}
 ],
 "flashcards": [
  {"front": "Ledger rule 1: what must the sum of all balances do?", "back": "Never change. A transfer moves money between accounts; it never creates or destroys any."},
  {"front": "Why must the balance check sit inside the same locks as the debit?", "back": "Otherwise it is check-then-act: another transfer can spend the money between the check and the debit, and the balance goes below zero."},
  {"front": "What stops `transfer(A, B)` and `transfer(B, A)` from deadlocking when each takes two locks?", "back": "One global lock order: always lock the account with the lower id first, whichever way the money moves."},
  {"front": "Why not order locks by `hashCode()`?", "back": "Two accounts can share a hash code. On a tie, two threads may lock in opposite orders. Use a unique id that never changes."},
  {"front": "How do you lock N accounts for one operation without deadlock?", "back": "Sort them by id, lock in that order, release in reverse. Call `distinct()` first if one account can appear twice."},
  {"front": "What does a record's compact constructor give a `Transfer`?", "back": "Checks that run before the fields are set, so every `Transfer` that exists is valid. With final fields, any thread sees it whole."},
  {"front": "A stress test checks only the final state. What can it miss?", "back": "Broken rules that heal: an account that went below zero and was topped up later. Also check each rule where it can break."}
 ],
 "terms": [
  {"term": "Ledger", "plain": "The bank's book of accounts and of every movement of money between them. In the lab, the class that holds the accounts and applies transfers."},
  {"term": "Invariant", "plain": "A rule about your data that must be true whenever another thread can look, such as \"the total never changes\"."},
  {"term": "Global lock order", "plain": "One rule, such as \"lower account id first\", that every piece of code follows when it takes more than one lock. It makes a cycle of waiting threads impossible."},
  {"term": "Lock granularity", "plain": "How much data one lock guards: the whole ledger, or one account. Finer locks let more work run at once, and they need a lock order."},
  {"term": "Compact constructor", "plain": "A record constructor without a parameter list. It runs before the fields are set, so it can check or clean up the values."},
  {"term": "Stress test", "plain": "A test that starts many threads at once, runs many operations, then checks the rules. It can find a race, but never prove there is none."},
  {"term": "Overdraft", "plain": "A debit that takes a balance below zero. In this ledger it is a bug, so `debit` refuses it."}
 ],
 "explain_back": {
  "prompt": "A reviewer looks at your `apply` and says: \"Why two locks and all this ordering? Put `synchronized` on the method and be done.\" Explain what that would give you, what it would cost, and why the balance check sits where it does.",
  "answer": "`synchronized` on `apply` locks the whole ledger, so every transfer waits for every other one. It is correct: it protects all three rules, and with one lock there is no order to get wrong. The cost is that transfers never overlap. A transfer between two accounts nobody else touches still waits in line, and at most one transfer is ever in progress. With one lock per account, transfers on different accounts run at the same time, at the price of a rule everyone must follow: lock the lower id first, or two opposite transfers can deadlock. Whether that overlap buys speed depends on the work inside the lock and on the free cores, so I'd measure it. I'd also avoid `synchronized` for code that virtual threads will call on JDK 21, where waiting at a `synchronized` block holds on to the carrier thread. Wherever the locks are, the balance check stays inside them: a check before them is check-then-act, and another transfer could spend the money between the check and the debit."
 },
 "deeper": {
  "minutes": 10,
  "body": """Two ways this design grows in a real bank.

The first is a busy account. Say one shop's account receives a third of all transfers. Every one of them waits for that account's single lock, whatever the order. A common fix is to split the account into a few smaller accounts, each with its own lock, credit a random one, and add them up when someone asks for the balance. For a single account, you could also drop the lock and use a compare-and-set loop, as Atomics and compare-and-set showed. The check becomes part of the loop:

```java
boolean debit(AtomicLong balance, long cents) {
    while (true) {
        long current = balance.get();
        if (current < cents) return false;                   // the check is inside the loop
        if (balance.compareAndSet(current, current - cents)) return true;
    }
}
```

```kotlin
fun debit(balance: AtomicLong, cents: Long): Boolean {
    while (true) {
        val current = balance.get()
        if (current < cents) return false                    // the check is inside the loop
        if (balance.compareAndSet(current, current - cents)) return true
    }
}
```

That works for one account without any lock. A transfer touches two, and two compare-and-sets in a row are not one step: between them, the money is in neither account, which breaks rule 3. That's why locks are the simpler tool for transfers.

The second is the database. A ledger kept on disk uses the same ideas with other tools: row locks taken in account id order, a `CHECK (balance >= 0)` rule on the table, and a unique key on the transfer id, so a transfer that arrives twice is applied once. Many real ledgers never change a balance in place at all. They add entries that never change, one debit and one credit per transfer, and compute each balance by adding up its entries. That's double-entry bookkeeping, a method traders and banks have used for centuries, and rule 1 becomes \"the entries of every transfer add up to zero\", which you can check one transfer at a time."""
 },
 "sources": [
  {"title": "ReentrantLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html"},
  {"title": "Java Language Specification, section 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10"},
  {"title": "Deadlock (The Java Tutorials)", "url": "https://docs.oracle.com/javase/tutorial/essential/concurrency/deadlock.html"},
  {"title": "Java Concurrency in Practice, Goetz et al., chapter 10 (lock ordering)", "url": "https://jcip.net/"}
 ]
}

out = ROOT / "content/lessons/cap1-01.json"
out.write_text(json.dumps(L, indent=1, ensure_ascii=False) + "\n")
print("wrote", out)
