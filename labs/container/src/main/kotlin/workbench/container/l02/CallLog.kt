package workbench.container.l02

import java.util.concurrent.CopyOnWriteArrayList

data class Call(val name: String, val nanos: Long, val failed: Boolean)

/** Where @Timed writes: one entry per call, in the order the calls finished. */
class CallLog {
    private val calls = CopyOnWriteArrayList<Call>()

    fun record(name: String, nanos: Long, failed: Boolean) {
        calls += Call(name, nanos, failed)
    }

    fun calls(): List<Call> = calls.toList()

    fun names(): List<String> = calls.map { it.name }
}
