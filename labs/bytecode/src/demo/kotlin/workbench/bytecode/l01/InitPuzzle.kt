package workbench.bytecode.l01

// Kotlin has no static fields of its own. An `object` and a companion object compile to a
// class with a static initializer, so the same JVM rules decide when the init blocks run.

open class KParent {
    companion object {
        @JvmField var parentValue = 1
        init { println("    KParent.<clinit>") }
    }
}

class KChild : KParent() {
    companion object {
        init { println("    KChild.<clinit>") }
    }
}

object KLimits {
    const val MAX_MINOR = 500_000             // a constant: kotlinc copies 500000 into callers
    val CAP: Int = 500_000                    // a property: reading it goes through KLimits
    init { println("    KLimits.<clinit>") }
}

object KLazy {
    init { println("    KLazy.<clinit>") }
    fun touch() {}
}

private fun step(what: String, s: () -> Any?) {
    println(what)
    s()
}

/** Predict which steps run a static initializer. Each one prints one indented line. */
fun main() {
    step("1. read KParent.parentValue") { KParent.parentValue }
    step("2. KChild()") { KChild() }
    step("3. read KLimits.MAX_MINOR") { KLimits.MAX_MINOR }
    step("4. read KLimits.CAP") { KLimits.CAP }
    step("5. arrayOfNulls<KLazy>(3)") { arrayOfNulls<KLazy>(3) }
    step("6. KLazy::class.java") { KLazy::class.java }
    step("7. Class.forName(name, false, loader)") {
        Class.forName("workbench.bytecode.l01.KLazy", false, KLazy::class.java.classLoader)
    }
    step("8. KLazy.touch()") { KLazy.touch() }
}
