package workbench.patterns.l07

// Template Method's sharpest edge, and the execute-around function that avoids it.

// classic Template Method: a skeleton with hooks for subclasses (Kotlin members are final unless open)
abstract class OutboundCall {
    private val label = "outbound " + name()       // calls a hook before the subclass has set its fields

    fun execute(): String {                        // the skeleton
        println("  start $label")
        try {
            return doCall()
        } finally {
            println("  end   $label")
        }
    }

    abstract fun name(): String                    // hook
    abstract fun doCall(): String                  // hook
}

class ChargeCall(private val psp: String) : OutboundCall() {   // psp is a non-null String...
    override fun name() = "charge via $psp"                    // ...and still reads as null here
    override fun doCall() = "ch_1250"
}

// execute around: the same skeleton as an inline function; the varying step is a lambda
inline fun <T> outbound(name: String, body: () -> T): T {
    println("  start $name")
    try {
        return body()
    } finally {
        println("  end   $name")
    }
}

fun main() {
    println("template: ${ChargeCall("northpay").execute()}")
    println("function: ${outbound("outbound charge via northpay") { "ch_1250" }}")
}
