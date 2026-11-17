package workbench.functional.l04.demo

// The sample baking day shared by the Kotlin demos of this lesson: five cookies on two trays.

enum class Status { GOLDEN, RAW, BURNT }

data class Cookie(
    val id: String,
    val flavor: String,
    val grams: Int,
    val status: Status,
    val nibbledGrams: Int? = null,      // someone took a bite
)

val sampleDay = listOf(
    Cookie("c1", "oat", 45, Status.GOLDEN),
    Cookie("c2", "chocolate", 90, Status.RAW),
    Cookie("c3", "oat", 50, Status.GOLDEN, nibbledGrams = 10),
    Cookie("c4", "ginger", 80, Status.BURNT),
    Cookie("c5", "chocolate", 30, Status.GOLDEN),
)
