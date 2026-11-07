package workbench.concurrency.scratch

import java.time.Instant
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.AtomicReference
import java.util.concurrent.atomic.LongAdder
import kotlin.concurrent.atomics.ExperimentalAtomicApi
import kotlin.concurrent.atomics.update

class S08Totals {
    private val authorized = AtomicLong()      // no lock needed

    fun onApproved(cents: Long) {
        authorized.addAndGet(cents)            // read, add, write: one indivisible step
    }

    fun total(): Long = authorized.get()       // a volatile read: sees the latest value
}

class S08Max {
    private val max = AtomicLong(Long.MIN_VALUE)
    private val balance = AtomicLong()

    fun offer(amount: Long) {
        var prev: Long
        do {
            prev = max.get()                        // 1. read
            if (amount <= prev) return              // 2. decide: nothing to do
        } while (!max.compareAndSet(prev, amount))  // 3. write only if max is still prev; else retry
    }

    fun library(amount: Long) {
        max.accumulateAndGet(amount, Math::max)           // the same loop, written for you
        balance.updateAndGet { b -> b + 100 }             // any pure function of the old value
    }
}

class S08Declines {
    private val declines = LongAdder()

    fun onDecline() = declines.increment()             // threads mostly hit different cells
    fun declinesSoFar(): Long = declines.sum()         // adds the cells up: not a snapshot
}

enum class S08State { CLOSED, OPEN }
data class Breaker(val state: S08State, val failures: Int, val openedAt: Instant?)   // immutable

class S08Breaker {
    private val breaker = AtomicReference(Breaker(S08State.CLOSED, 0, null))

    fun onFailure(now: Instant) {
        breaker.updateAndGet { b ->
            if (b.failures + 1 >= 5) Breaker(S08State.OPEN, b.failures + 1, now)   // trip
            else b.copy(failures = b.failures + 1)
        }
    }
}

class S08Node<T>(val item: T, val next: S08Node<T>?)
class S08Stack<T> {
    private val head = AtomicReference<S08Node<T>?>(null)

    fun push(item: T) {
        var top: S08Node<T>?
        var node: S08Node<T>
        do {
            top = head.get()
            node = S08Node(item, top)           // build the new node off to the side
        } while (!head.compareAndSet(top, node))  // publish it only if head is still top
    }
}

class S08Limit(private val limit: Long) {
    private val spent = AtomicLong()

    fun tryAuthorizeLoop(cents: Long): Boolean {
        while (true) {
            val before = spent.get()                       // 1. read the current spend
            if (before + cents > limit) return false       // 2. decide on that value
            if (spent.compareAndSet(before, before + cents)) return true   // 3. commit, if unchanged
        }                                                  // 4. lost the race: re-read, decide again
    }

    fun tryAuthorize(cents: Long): Boolean {
        val before = spent.getAndUpdate { s -> if (s + cents <= limit) s + cents else s }
        return before + cents <= limit                     // did OUR update apply?
    }

    fun broken(cents: Long): Boolean {
        if (spent.get() + cents <= limit) {               // check
            spent.addAndGet(cents)                         // act
            return true
        }
        return false
    }
}

@OptIn(ExperimentalAtomicApi::class)
class S08KotlinAtomics {
    private val max = kotlin.concurrent.atomics.AtomicLong(Long.MIN_VALUE)

    fun offer(amount: Long) {
        max.update { prev -> maxOf(prev, amount) }     // a CAS loop inside, like updateAndGet
    }
}

@OptIn(ExperimentalAtomicApi::class)
class S08CompareMax {
    private val max = kotlin.concurrent.atomics.AtomicLong(Long.MIN_VALUE)   // kotlin.concurrent.atomics, not java.util

    fun offer(amount: Long) {
        max.update { prev -> maxOf(prev, amount) }  // a CAS loop inside, like updateAndGet
    }

    fun max(): Long = max.load()
}

fun s08Drill(tokens: java.util.concurrent.atomic.AtomicInteger): Boolean {
    while (true) {
        val left = tokens.get()
        if (left == 0) return false                        // nothing left: no write
        if (tokens.compareAndSet(left, left - 1)) return true
    }                                                      // someone else took one: retry
}
