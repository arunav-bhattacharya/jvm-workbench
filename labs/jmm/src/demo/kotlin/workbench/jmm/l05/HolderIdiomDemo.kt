package workbench.jmm.l05

/** When does each singleton get built? Watch the order of the lines. */

// eager: a companion object is initialized together with its class
private class EagerBins private constructor() {
    init { println("     EagerBins built") }
    companion object {
        val INSTANCE = EagerBins()
        fun tableSize() = 3
    }
}

// holder idiom in Kotlin: a private nested object is initialized on first access
private class LazyBins private constructor() {
    init { println("     LazyBins built") }
    private object Holder {
        val INSTANCE = LazyBins()
    }
    companion object {
        fun instance(): LazyBins = Holder.INSTANCE
        fun tableSize() = 3
    }
}

// Kotlin's own answer: an object declaration, built on first access and thread-safe
private object BinTable {
    init { println("     BinTable built") }
    fun tableSize() = 3
}

fun main() {
    println("1. call EagerBins.tableSize()")
    EagerBins.tableSize()
    println("2. call LazyBins.tableSize()")
    LazyBins.tableSize()
    println("3. call LazyBins.instance()")
    LazyBins.instance()
    println("4. call LazyBins.instance() again")
    LazyBins.instance()
    println("5. call BinTable.tableSize()")
    BinTable.tableSize()
}
