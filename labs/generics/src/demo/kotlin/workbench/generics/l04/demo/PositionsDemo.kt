package workbench.generics.l04.demo

/** Which members may mention T in a class declared `out T`? Uncomment ONE line at a time and run. */
interface Producer<out T> {
    fun produce(): T                         // return type: out-position, fine
    val latest: T                            // val: out-position, fine
    // fun consume(item: T)                  // 1
    // var current: T                        // 2
}

class Holder<out T>(val item: T, plain: T, private var hidden: T) {   // all three are fine
    private fun replace(t: T) { hidden = t }                            // private: exempt
    fun first(): T = item
    // protected fun keep(t: T) {}                                     // 3
}

// class Mutable<out T>(var item: T)                                    // 4

fun main() {
    val h: Holder<Any> = Holder("EUR", "x", "y")
    println("Holder<String> used as Holder<Any>: ${h.first()}")
}
