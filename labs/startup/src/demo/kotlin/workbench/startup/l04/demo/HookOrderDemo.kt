package workbench.startup.l04.demo

/**
 * A toy checkpoint: three components register hooks in the order the service creates them.
 * Pass "leak" as an argument and the metrics reporter forgets to close its socket.
 */
private interface Hooks {                               // org.crac.Resource: the same two methods, plus a Context argument
    fun beforeCheckpoint()
    fun afterRestore()
}

private val registered = mutableListOf<Hooks>()
private val openSockets = mutableListOf<String>()

private class Component(val name: String, val leaks: Boolean) : Hooks {
    init {
        openSockets += name                             // every component holds a connection
        registered += this                              // and registers itself when it is created
    }

    override fun beforeCheckpoint() {
        println("  beforeCheckpoint: $name")
        if (!leaks) openSockets -= name
    }

    override fun afterRestore() {
        println("  afterRestore:     $name")
        if (name !in openSockets) openSockets += name
    }
}

fun main(args: Array<String>) {
    val leak = args.firstOrNull() == "leak"
    Component("ledger DB pool", false)                  // created first: the others use it
    Component("Kafka consumer", false)
    Component("metrics reporter", leak)

    println("checkpoint requested")
    registered.asReversed().forEach { it.beforeCheckpoint() }          // last registered first
    if (openSockets.isEmpty()) {
        println("  -- snapshot written --")
    } else {
        println("  -- checkpoint refused, still open: $openSockets --")
    }
    registered.forEach { it.afterRestore() }                           // first registered first
}
