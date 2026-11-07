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
    '<rect class="box" x="535" y="56" width="95" height="36" rx="8"/><text class="t" x="582" y="79" text-anchor="middle">unlock</text>'
    '<line class="ln" x1="265" y1="74" x2="283" y2="74" marker-end="url(#arr)"/>'
    '<line class="ln" x1="390" y1="74" x2="408" y2="74" marker-end="url(#arr)"/>'
    '<line class="ln" x1="515" y1="74" x2="533" y2="74" marker-end="url(#arr)"/>'
    '<text class="t" x="20" y="162">T2</text><text class="t-s t-m" x="20" y="180">acc-03 to acc-07</text>'
    '<rect class="box-dim" x="160" y="146" width="355" height="36" rx="8"/>'
    '<text class="t-s" x="337" y="169" text-anchor="middle">waits for 03, holding nothing</text>'
    '<rect class="box-a" x="535" y="146" width="95" height="36" rx="8"/><text class="t t-code" x="582" y="169" text-anchor="middle">lock 03</text>'
    '<line class="ln-d" x1="582" y1="92" x2="582" y2="144" marker-end="url(#arr)"/>'
    '<text class="t-s t-ok" x="337" y="222" text-anchor="middle">one order for both: contention, never a cycle</text>'
    '</svg>')

L = {
 "id": "cap1-01",
 "title": "Design the ledger and make it correct",
 "minutes": 40,
 "goal": "By the end you can write down a ledger's invariants before its code, protect them with per-account locks taken in one global order, model a transfer as an immutable value, and test the invariants with a stress harness of 8 threads x 100,000 transfers.",
 "warmup": {
  "q": "A ledger holds 50 accounts with 500,000 cents in total. Eight threads make 100,000 random transfers each with `if (balance[from] >= c) { balance[from] -= c; balance[to] += c; }` on a plain `long[]`, with no locks. What is the total at the end?",
  "options": ["Exactly 500,000, because every transfer adds what it subtracts",
              "Some other number, different on every run",
              "Exactly 500,000, but some balances are negative",
              "The JVM throws a ConcurrentModificationException"],
  "answer": 1,
  "why": "Each `-=` and `+=` is a read, a change and a write. When two threads update the same account at the same moment, one of the two updates is lost. A lost debit creates money and a lost credit destroys it, so the total drifts, by millions of cents in the demo below. Nothing throws: a plain array has no checks at all."
 },
 "sections": [
  {
   "h": "Write the invariants down before the code",
   "body": """Here is the smallest ledger that can be wrong. Fifty accounts, no locks:

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

Run it on eight threads with 100,000 random transfers each, and the total is wrong by millions of cents. You know the mechanism from *Race conditions: why count++ lies*: `-=` is a read, a subtraction and a write, and two threads that read the same balance lose one of the two updates.

Before you write the real ledger, write down what correct means. An **invariant** is a statement about the data that must be true whenever another thread can look. This ledger has three:

1. Money is conserved: the sum of all balances never changes.
2. No balance is ever below zero.
3. A transfer happens whole or not at all: nobody sees the debit without the credit.

Each invariant decides part of the design. Invariants 1 and 3 say the debit and the credit must be one step that no other thread can split, and that step spans *two* accounts. Invariant 2 says the balance check belongs inside that same step. A check in one step and a debit in another is check-then-act, the second race shape from that lesson. And "whenever another thread can look" tells you where to test: not only at the end of a run.

The rest of this lesson builds the ledger so that every line of `apply` points at one of these three. That is the habit to keep for any shared state: invariants first, then the locks that protect them, then a test that tries hard to break them.""",
   "try": {
    "title": "Count what a lock-free ledger loses",
    "minutes": 3,
    "steps": [
     "Open `BrokenLedgerDemo` (or its Kotlin twin). Before you run it, write down what you expect the total to be after each run.",
     "Run it with the command below. Note how far off each run is.",
     "Run it again with `-Pargs=1000`, so each thread makes only 1,000 transfers. The threads still start behind a latch. Predict first: will the total be right?"
    ],
    "code": demo("BrokenLedgerDemo"),
    "expect": "With 100,000 transfers per thread the total is off by millions of cents, and by a different amount every run (one run here ended at 5,222,671 cents instead of 500,000). With 1,000 per thread it is still wrong, by thousands: the latch releases all eight threads at the same moment, so even short runs collide. Without the latch, short runs often look correct because each thread finishes before the next one starts."
   }
  },
  {
   "h": "A transfer is a value, so make it immutable",
   "body": """A transfer crosses threads. An HTTP handler or a file importer builds it, a pool thread applies it, the journal writes it and a log line prints it. If any of them can change it, the others can see two versions of it.

Here is that bug in its most common form. A batch importer parses a file into one reusable row object, to save allocations, and hands each row to a pool:

```java
TransferRow row = new TransferRow();             // mutable, reused for every line
for (String line : file) {
    row.parse(line);                             // overwrites id, from, to, cents
    pool.execute(() -> ledger.apply(row));       // a worker reads row later
}
```

```kotlin
val row = TransferRow()                          // mutable, reused for every line
for (line in file) {
    row.parse(line)                              // overwrites id, from, to, cents
    pool.execute { ledger.apply(row) }           // a worker reads row later
}
```

By the time a worker reads `row`, the parser has moved on. In this section's demo, 100,000 lines reached the ledger as about 11,000 different transfers, most of them applied several times. A few dozen rows carried the id of one line and the amount of another. That is a data race: the worker read the fields with no happens-before edge to the parser's later writes, so it could see any mix of them.

The fix is a value that can't change. A Java record, or a Kotlin `data class` of `val`s, has final fields and no setters:

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

Two things come with it. As *Safe publication, final fields and escaping this* showed, an object with only final fields that doesn't leak `this` is seen whole by any thread, however it gets there. And the checks run once, at construction, so a `Transfer` that exists is valid. The ledger never asks whether `cents` is negative or `from` equals `to`, and the lock-ordering code in the next section relies on two different accounts.

Money is a `long` of cents. A `double` can't hold 0.10 exactly, and a ledger that drifts by fractions of a cent breaks invariant 1 with no thread involved.""",
   "try": {
    "title": "Reuse one row, then use a record",
    "minutes": 3,
    "steps": [
     "Run `ReusedTransferDemo`. It parses 100,000 lines and hands each one to a pool of 4 threads. Predict first: how many different lines reach the ledger?",
     "Run it again with `-Pargs=record`, which builds a new immutable `Transfer` for each line."
    ],
    "code": demo("ReusedTransferDemo"),
    "expect": "With the reused row only a fraction of the lines arrive (between 10,000 and 13,000 in runs here), the cents don't add up, and a few dozen rows mix one line's id with another line's amount. With a record all 100,000 lines arrive, the totals match and nothing is mixed. Each record is built once, handed to the pool (an executor hand-off is a happens-before edge), and never written again."
   },
   "refs": [
    {"title": "Java Language Specification, section 8.10: Record classes", "url": "https://docs.oracle.com/javase/specs/jls/se25/html/jls-8.html#jls-8.10", "kind": "docs"}
   ]
  },
  {
   "h": "Per-account locks, taken in one global order",
   "body": """Invariants 1 and 3 need the debit and the credit to happen as one step. The simplest way is one lock for the whole ledger. It is correct, and it makes two transfers that share no account wait for each other. With one lock per account, a transfer between accounts 3 and 7 and another between 12 and 40 can run at the same time.

Per-account locks bring back the bug from *Deadlock, livelock and starvation*: a transfer from A to B locks A and waits for B, while a transfer from B to A holds B and waits for A. The fix from that lesson applies as it is. Give every account a unique, stable key and always lock the smaller key first:

```java
public Outcome apply(Transfer t) {
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
}
```

```kotlin
fun apply(t: Transfer): Outcome {
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
    }                                                                      // 4. withLock unlocks in finally
}
```

Each line traces back to an invariant. The order (1) removes the cycle that a deadlock needs. The check sits under both locks (2), so no other transfer can spend the same money between the check and the debit. Debit and credit share one critical section (3), so a thread that takes these locks never sees half a transfer. And `finally` (4) releases both locks on every path, including the early return for a refusal.

The account id is a `String` compared with `compareTo`. It is unique and never changes, and that is all an order needs. `hashCode()` would not do: two accounts can share a hash code, and then two threads can disagree about which one comes first.

Why `ReentrantLock` and not `synchronized`? Here they behave the same. The choice pays off in lesson 3 of this track: on JDK 21, a virtual thread waiting to enter a `synchronized` block holds on to its carrier thread, and a ledger serving 10,000 virtual threads will have waiters.

What do per-account locks buy? Run the demo and count. With one lock, at most one transfer is ever in progress. With per-account locks, about as many as you have cores. Whether that also makes it faster depends on how much work sits inside the lock and on what else your machine is doing, so the demo prints both.""",
   "figure": {"svg": FIGURE, "caption": "T1 and T2 move money in opposite directions, and both lock acc-03 first. T2 waits for that lock while holding nothing, so no cycle can form."},
   "try": {
    "title": "Count the transfers in progress",
    "minutes": 4,
    "steps": [
     "Run `LockGranularityDemo`. It runs the same 400,000 random transfers under one ledger-wide lock, then under per-account locks taken in id order. Each transfer does 50 steps of work inside its lock.",
     "Before you read the output, predict the last column, \"most transfers in progress at once\", for each strategy.",
     "Run it with `-Pargs=0` (no work inside the lock) and with `-Pargs=200`. Compare the times, and explain any surprise."
    ],
    "code": demo("LockGranularityDemo"),
    "expect": "With one lock the last column is always 1. With per-account locks it shows about as many as your cores (4 or 5 on the 4-core machine used here; a thread paused by the OS inside a lock still counts). The times vary with your machine and its load. On the busy machine used here the per-account version was faster in some runs and slower in others, and with `-Pargs=0` the single lock often won, because handing a lock from thread to thread costs more than the few instructions it guards. The total is 500,000 in every row: both strategies keep the invariants."
   },
   "refs": [
    {"title": "ReentrantLock (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/locks/ReentrantLock.html", "kind": "docs"}
   ]
  },
  {
   "h": "A stress harness that tests every invariant",
   "body": """A stress test for the ledger has to make threads collide, then check every invariant. *Testing and debugging concurrent code* listed the habits: a start line so the threads overlap, more threads than cores, many operations, and checks after `join()`. The lab's harness runs 8 threads that each make 100,000 random transfers between 50 accounts:

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

After the joins, the test checks: the total is still 500,000, no balance is negative, applied plus refused is 800,000 so no transfer vanished, and some transfers were refused, which proves the overdraft branch ran at all.

That list has a hole, and this section's demo falls into it. Take a ledger that locks in id order but checks the balance *before* it takes the locks. Money is still conserved, because each move is atomic. Balances look fine at the end, because a later credit usually tops up an account that went negative. Yet while it ran, thousands of debits took an account below zero. An end-of-run check sees a healthy ledger.

So check each invariant where it can break, as well as at the end. The lab's `Account.debit` throws `IllegalStateException` when a debit would overdraw, so a race that overdraws fails the stress test at once. The check costs one comparison, and in production it turns a silent loss into an error that pages someone. In a database, a `CHECK (balance >= 0)` constraint does the same job.

Then remember what a pass means. Eight threads and 800,000 transfers that find nothing make the ledger more believable. They don't prove it. The proof is the argument you can make for each invariant from the code, which is why you wrote the invariants down first.""",
   "try": {
    "title": "Find the bug that conserves money",
    "minutes": 4,
    "steps": [
     "Read `CheckOutsideLockDemo`. Both ledgers lock accounts in id order. The first checks the balance, looks up a fee, then takes the locks and moves the money. The second takes the locks, then checks.",
     "Predict which invariants each version breaks, then run it.",
     "Find the line that counts overdrafts. Explain why the \"negative at the end\" column misses what it counts."
    ],
    "code": demo("CheckOutsideLockDemo"),
    "expect": "Both totals are 500,000 and neither ledger ends with a negative balance. The first one still overdrew accounts a few thousand times while it ran (3,537 times in one run here); the second never did. Each move was atomic, so invariant 1 held. Invariant 2 broke in the gap between the check and the locks, and later credits hid the evidence before the end."
   },
   "refs": [
    {"title": "CountDownLatch (Java SE 25 API)", "url": "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/concurrent/CountDownLatch.html", "kind": "docs"}
   ]
  }
 ],
 "analogy": "Picture a vault room where every safe-deposit box has its own key on a numbered hook. A clerk who moves cash between two boxes must hold both keys while doing it, and the house rule says: take the lower-numbered key first. Two clerks who both need boxes 3 and 7 never end up each holding one key and waiting for the other; one of them waits at hook 3 with empty hands. One key for the whole room would also be correct, and every clerk would queue at the door. The analogy breaks in one place: a real clerk who opens a box and finds it short of cash stops. A thread checks only what your code tells it to check, at the moment you tell it, which is why the check has to sit inside the locks.",
 "in_your_world": "Your payment services lean on the same invariants, usually through the database: `SELECT ... FOR UPDATE` on two account rows, a `CHECK (balance >= 0)` constraint, a unique key on the transfer id. Row locks deadlock exactly like Java locks when two transactions lock the same two rows in opposite orders, and the database then fails one of them with a deadlock error. The fix is the same global order: lock the rows sorted by account id. An in-memory ledger like this one shows up in front of the database: a wallet balance cache, a per-merchant spend limit, the local state of a Temporal workflow. And a Kafka consumer that reuses one mutable DTO per record has the importer's bug the day someone hands records to a pool.",
 "mistake": "The most common real mistake is checking the balance in one step and moving the money in another: read the balance (often under the account's lock), decide, then lock both accounts and transfer. Each step is thread-safe, so the code looks careful. It is check-then-act across two critical sections, and another transfer can spend the same money in between. It hides well, because money is still conserved and later credits cover the overdraft before any end-of-day report runs. The fix is to put the check inside the critical section that moves the money, and to guard the invariant where it can break: a debit that would overdraw throws.",
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
  "note": "Kotlin's `withLock` is an inline function that calls `lock()`, runs the block and calls `unlock()` in a `finally`, so the two nested `try`/`finally` blocks become two nested lambdas. Because it is inline, `return Outcome.INSUFFICIENT_FUNDS` inside the block returns from `apply` itself, and the locks are still released. `from.id < to.id` on strings calls the same `compareTo` as the Java version. The immutable `Transfer` differs only in style: a Kotlin `data class` of `val`s is exactly as shallow as a Java record. Both make the fields final, and neither copies a mutable list you pass in."
 },
 "worked": {
  "title": "Add a fee without breaking the invariants",
  "steps": [
   {"say": "The product team wants a fee on each transfer, paid into a fee account. Money is still conserved: the sender pays `cents + fee`, the receiver gets `cents` and the fee account gets `fee`. Three accounts now change in one step. Here is the first attempt. Read it against the three invariants and the lock order before you go on.",
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
   {"say": "Two bugs. The locks are ordered by role, not by id: a transfer from acc-02 to acc-05 locks 02 then 05, while a transfer from acc-05 to acc-02 locks 05 then 02. That is the deadlock cycle again. And the check tests `cents`, but the debit takes `cents + fee`, so a sender with exactly `cents` left goes below zero. The lab's `debit` would throw; a plain field would quietly go negative.", "code": "", "lang": ""},
   {"say": "Sort every account the operation touches by id, lock them in that order, and release them in reverse. The same code works for two accounts, three, or a payroll batch of fifty. `distinct()` covers the case where the sender is the fee account itself, because a `ReentrantLock` taken twice must also be released twice.",
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
   {"say": "Check it against the invariants. Conservation: the sender loses `cents + fee` and the other two gain exactly that. No overdraft: the check and the debit use the same amount under the same locks. Whole or nothing: all three changes happen inside one set of locks. No deadlock: plain `apply` locks two accounts in id order and this method locks three in id order, so any two operations agree on which lock comes first. Where the fee account's id sorts among the customer ids doesn't matter. Only the rule matters.", "code": "", "lang": ""}
  ]
 },
 "lab": {
  "title": "Build the ledger and the harness that tries to break it",
  "minutes": 15,
  "files": [f"{lab}/main/{P}/Transfer.java", f"{lab}/main/{P}/Ledger.java", f"{lab}/main/{P}/StressHarness.java", f"{lab}/main/{P}/Account.java"],
  "run": "./gradlew :ledger:test --tests 'workbench.ledger.l01.*'",
  "steps": [
   "Run the tests once. All nine fail. Read `Account`: you don't change it, but its `debit` and `credit` throw unless you hold that account's lock, and `debit` throws on an overdraft.",
   "In `Transfer`, add a compact constructor: `Objects.requireNonNull` for `id`, `from` and `to`, and an `IllegalArgumentException` when `cents <= 0` or `from.equals(to)`.",
   "Write `Ledger.apply`: look up both accounts, pick `first` and `second` with `id().compareTo`, lock them in that order with nested `try`/`finally`, then check the balance and move the money while you hold both locks.",
   "Write `StressHarness.run`: a `ready` latch and a `go` latch, `threads` workers that each make `perThread` random transfers with `ThreadLocalRandom`, per-thread counts stored in a `long[]` slot at the end, then join every worker and add up the slots.",
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
  "Write the invariants first: money is conserved, no balance goes below zero, a transfer is whole or not at all. Every line of `apply` protects one of them.",
  "Debit and credit happen in one critical section that holds both accounts' locks, and the balance check sits inside it too. Anything else is check-then-act.",
  "Lock accounts in one global order by a unique, stable id (`compareTo`, never `hashCode`). For more than two accounts, sort them all, lock in order, release in reverse.",
  "A transfer is an immutable value checked in its constructor: safe to hand to any thread, and never invalid. A reused mutable row handed to a pool delivers the wrong data.",
  "A stress harness needs a start line, more threads than cores, many operations, and checks of every invariant, both at the end and where each one can break.",
  "Per-account locks let transfers on different accounts run at once. With little work inside the lock one lock can be as fast, so count and measure before you argue."
 ],
 "quiz": [
  {"q": "A teammate orders the two locks in `apply` by `System.identityHashCode(account)` instead of by account id. What can go wrong?",
   "options": ["Nothing: every object has a different identity hash code",
               "Two accounts can share a hash code, and then two transfers may lock them in opposite orders and deadlock",
               "The hash code changes when the GC moves the object, so the order changes",
               "Nothing serious: ReentrantLock detects the deadlock and throws"],
   "answer": 1,
   "why": "Identity hash codes are not unique. On a tie neither account sorts first, so one thread may lock A first and another B first, which is the cycle. *Java Concurrency in Practice* breaks the tie with an extra global lock; a unique account id avoids the problem. The identity hash code stays the same for the object's life even when the GC moves it, and no lock detects a deadlock for you.",
   "from": "conc-06"},
  {"q": "This `apply` locks both accounts in id order, but first it calls `if (balanceOf(from) < cents) return INSUFFICIENT_FUNDS;`, which takes and releases `from`'s lock. Eight threads stress it. Which invariant can break?",
   "options": ["A balance can go below zero",
               "Money is no longer conserved",
               "Two opposite transfers can deadlock",
               "None: every step holds a lock"],
   "answer": 0,
   "why": "It's check-then-act: another transfer can spend the money between `balanceOf` and the locks. Each move is still atomic, so the total is conserved, which is exactly why a test that only checks totals passes. Locks taken in id order can't deadlock. \"Every step holds a lock\" is the trap: two atomic steps in a row are not one atomic step.",
   "from": "conc-03"},
  {"q": "`record Transfer(String id, List<String> tags, long cents)`. The importer fills an `ArrayList` of tags, builds the record, submits it to a pool, then clears the list and reuses it for the next line. What can the worker see in `tags()`?",
   "options": ["The original tags, because records are immutable",
               "A copy, because records copy their components",
               "An empty or half-changed list, because the record holds the importer's list object",
               "Nothing: `clear()` throws UnsupportedOperationException"],
   "answer": 2,
   "why": "Records are shallowly immutable. The field can't point at another list, but the list itself is the importer's `ArrayList`, and clearing it changes what the worker reads. Copy it in the compact constructor with `tags = List.copyOf(tags)`, which also gives the record an unmodifiable list. Records never copy their components for you.",
   "from": "conc-11"},
  {"q": "The ledger's stress test passed 50 runs in a row on your laptop. What have you shown?",
   "options": ["The ledger is thread-safe",
               "The ledger is thread-safe on x86, but maybe not on ARM",
               "The JIT compiled the race away",
               "These runs found no failure; the argument that each invariant holds has to come from the code"],
   "answer": 3,
   "why": "A stress test can show that a race exists, never that none does. Fifty clean runs with a start latch and many threads make a bug less likely. The proof is the reasoning: which lock guards which field, and why each invariant holds inside the critical section.",
   "from": "conc-13"},
  {"q": "Which change to the ledger breaks invariant 3, \"a transfer happens whole or not at all\"?",
   "options": ["Locking `to` first whenever `to` has the lower id",
               "Replacing the `ReentrantLock`s with `synchronized` blocks taken in the same order",
               "Debiting inside one locked block, releasing both locks, then crediting inside a second locked block",
               "Making `Transfer` a Kotlin data class instead of a Java record"],
   "answer": 2,
   "why": "Between the two blocks, a thread that locks both accounts (a snapshot, an audit) sees the money gone from one account and not yet in the other, and an exception at that point loses it. The other changes keep debit and credit in one critical section: locking the lower id first is the rule itself, `synchronized` gives the same exclusion, and a data class is as immutable as a record."}
 ],
 "flashcards": [
  {"front": "Ledger invariant 1: what must the sum of all balances do?", "back": "Never change. A transfer moves money between accounts; it never creates or destroys any."},
  {"front": "Why must the balance check sit inside the same locks as the debit?", "back": "Otherwise it is check-then-act: another transfer can spend the money between the check and the debit, and the balance goes negative."},
  {"front": "What stops `transfer(A, B)` and `transfer(B, A)` from deadlocking when each takes two locks?", "back": "A global lock order: always lock the account with the lower id first, whichever way the money moves."},
  {"front": "Why not order locks by `hashCode()`?", "back": "Two accounts can share a hash code. On a tie, two threads may lock in opposite orders. Use a unique, stable id."},
  {"front": "How do you lock N accounts for one operation without deadlock?", "back": "Sort them by id, lock in that order, release in reverse. `distinct()` first, if one account can appear twice."},
  {"front": "What does a record's compact constructor give a `Transfer`?", "back": "Checks that run before the fields are set, so every `Transfer` that exists is valid. With final fields, any thread sees it whole."},
  {"front": "A stress test checks only the final state. What can it miss?", "back": "Violations that heal: an account that went negative and was topped up later. Also check each invariant where it can break."}
 ],
 "terms": [
  {"term": "Invariant", "plain": "A statement about your data that must be true whenever another thread can look, such as \"the total never changes\"."},
  {"term": "Global lock order", "plain": "One rule, such as \"lower account id first\", that every code path follows when it takes more than one lock. It makes a wait cycle impossible."},
  {"term": "Lock granularity", "plain": "How much data one lock guards: the whole ledger, or one account. Finer locks let more work run at once and need a lock order."},
  {"term": "Compact constructor", "plain": "A record constructor without a parameter list. It runs before the fields are assigned, so it can check or normalize the values."},
  {"term": "Stress harness", "plain": "A test driver that starts many threads at once, runs many operations, then checks the invariants."},
  {"term": "Overdraft", "plain": "A debit that takes a balance below zero. In this ledger it is a bug, so `debit` refuses it."}
 ],
 "explain_back": {
  "prompt": "A reviewer looks at your `apply` and says: \"Why two locks and all this ordering? Put `synchronized` on the method and be done.\" Explain what that would give you, what it would cost, and why the balance check sits where it does.",
  "answer": "`synchronized` on `apply` locks the whole ledger, so every transfer waits for every other one. It is correct: it protects all three invariants, and with one lock there is no order to get wrong. The cost is parallelism. A transfer between two accounts nobody else touches still waits in line, and at most one transfer is ever in progress. With per-account locks, transfers on different accounts run at the same time, at the price of a rule everyone must follow: lock the lower id first, or two opposite transfers can deadlock. Whether that parallelism buys speed depends on the work inside the lock and on the cores you have, so I'd measure it. On JDK 21 I'd also avoid `synchronized` for code that virtual threads will call. Wherever the locks are, the balance check stays inside them: a check before them is check-then-act, and another transfer could spend the money between the check and the debit."
 },
 "deeper": {
  "minutes": 10,
  "body": """Two directions this design grows in real systems.

The first is hot accounts. A merchant settlement account that receives a third of all transfers serializes them on its one lock, whatever the order. A common fix is to split it into a few sub-accounts, each with its own lock, credit a random one, and add them up for the balance. For a single account you could also drop the lock and use a compare-and-set loop, as *Atomics and compare-and-set* showed. The check becomes part of the loop:

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

That is lock-free for one account. A transfer touches two, and two compare-and-sets in a row are not one atomic step: between them the money is in neither account, which breaks invariant 3. That is why locks are the simpler tool for transfers.

The second is the database. A persisted ledger uses the same ideas with other tools: row locks taken in account id order, a `CHECK (balance >= 0)` constraint, and a unique key on the transfer id so a retried request applies once. Many ledgers never update a balance in place at all. They append immutable entries, one debit and one credit per transfer, and compute balances from them. That is double-entry bookkeeping, and invariant 1 becomes \"the entries of every transfer sum to zero\", which you can check one transfer at a time."""
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
