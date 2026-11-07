package workbench.jmm.l06

import java.lang.invoke.MethodHandles
import java.lang.invoke.VarHandle
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread

/*
 * One producer hands transfers to one consumer through a one-item slot, for three seconds.
 * The argument picks the slot: plain (ordinary property access), opaque, or release (the default).
 */
private class Transfer { var id = 0L; var amountCents = 0L }   // plain fields on purpose

private interface Slot {
    fun offer(t: Transfer): Boolean   // producer only: false if the slot is still full
    fun poll(): Transfer?             // consumer only: null if the slot is empty
}

private open class Box {
    var item: Transfer? = null        // null means empty

    companion object {
        val ITEM: VarHandle = MethodHandles.lookup().findVarHandle(Box::class.java, "item", Transfer::class.java)
    }
}

private class PlainSlot : Box(), Slot {   // what ordinary Kotlin code does
    override fun offer(t: Transfer): Boolean {
        if (item != null) return false
        item = t
        return true
    }
    override fun poll(): Transfer? {
        val t = item
        if (t != null) item = null
        return t
    }
}

private class OpaqueSlot : Box(), Slot {
    override fun offer(t: Transfer): Boolean {
        if (ITEM.getOpaque(this) != null) return false
        ITEM.setOpaque(this, t)
        return true
    }
    override fun poll(): Transfer? {
        val t = ITEM.getOpaque(this) as Transfer?
        if (t != null) ITEM.setOpaque(this, null)
        return t
    }
}

private class ReleaseAcquireSlot : Box(), Slot {
    override fun offer(t: Transfer): Boolean {
        if (ITEM.getAcquire(this) != null) return false
        ITEM.setRelease(this, t)                          // release: t's fields were written before this
        return true
    }
    override fun poll(): Transfer? {
        val t = ITEM.getAcquire(this) as Transfer?        // acquire: so the consumer sees them
        if (t != null) ITEM.setRelease(this, null)
        return t
    }
}

fun main(args: Array<String>) {
    val mode = args.firstOrNull() ?: "release"
    val slot: Slot = when (mode) {
        "plain" -> PlainSlot()
        "opaque" -> OpaqueSlot()
        else -> ReleaseAcquireSlot()
    }
    val handed = AtomicLong()   // progress, for main to watch
    val wrong = AtomicLong()

    thread(isDaemon = true) {   // daemon, so the JVM can exit even if it spins forever
        var id = 1L
        while (true) {
            val t = Transfer()
            t.id = id                                    // 1. fill in the message with plain writes
            t.amountCents = id * 7
            while (!slot.offer(t)) { }                   // 2. spin until the slot is empty, then hand it over
            id++
        }
    }
    thread(isDaemon = true) {
        var expected = 1L
        while (true) {
            var t = slot.poll()
            while (t == null) t = slot.poll()            // 3. spin until the slot is full
            if (t.id != expected || t.amountCents != expected * 7) wrong.incrementAndGet()
            handed.set(expected)
            expected++
        }
    }

    var last = -1L
    repeat(4) {
        Thread.sleep(750)
        val now = handed.get()
        if (now == last) {
            println("%s: stuck after %,d handoffs. A spinning thread stopped seeing the slot change.".format(mode, now))
            return
        }
        last = now
    }
    println("%s: %,d transfers handed over in 3 s, %,d with wrong fields".format(mode, handed.get(), wrong.get()))
}
