package workbench.generics.l08.demo

fun main() {
    // 1. Two different types, one class at run time.
    val ids = ArrayList<String>()
    val cents = ArrayList<Int>()
    println("same class at run time: ${ids.javaClass == cents.javaClass} (${ids.javaClass.name})")

    // 2. An unchecked cast succeeds, because only the class can be checked.
    @Suppress("UNCHECKED_CAST")
    val lies = listOf(1_200, 350) as Any as List<String>
    println("the cast worked, size = ${lies.size}")

    // 3. The failure comes later, where a String is finally needed.
    try {
        val first: String = lies[0]
        println(first)
    } catch (e: ClassCastException) {
        println("ClassCastException at the read: ${e.message?.substringBefore(" (")}")
    }

    // Wrong move 1. Uncomment, predict the error, then run.
    // println((ids as Any) is List<String>)
}

// Wrong move 2: make a T without knowing what T is.
// fun <T> make(): T = T()
