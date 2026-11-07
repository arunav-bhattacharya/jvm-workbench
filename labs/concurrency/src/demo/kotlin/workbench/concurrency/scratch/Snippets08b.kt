package workbench.concurrency.scratch

import java.lang.invoke.MethodHandles
import java.lang.invoke.VarHandle

class S08Account {
    @Volatile private var spent = 0L

    fun add(expected: Long, next: Long): Boolean =
        SPENT.compareAndSet(this, expected, next)        // CAS on this object's field

    fun spent() = spent

    companion object {
        private val SPENT: VarHandle = MethodHandles.privateLookupIn(S08Account::class.java, MethodHandles.lookup())
            .findVarHandle(S08Account::class.java, "spent", Long::class.java)
    }
}

fun main() {
    val a = S08Account()
    println("cas 0->5: ${a.add(0, 5)}, cas 0->7: ${a.add(0, 7)}, spent=${a.spent()}")
}
