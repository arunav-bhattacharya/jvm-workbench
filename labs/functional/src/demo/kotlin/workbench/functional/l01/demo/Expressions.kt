package workbench.functional.l01.demo

// A recipe book marks each recipe with one, two or three stars.
enum class Difficulty { EASY, MEDIUM, HARD }

// Statement style: declare a var, then assign it in every branch and hope you didn't miss one.
fun difficultyStatement(stars: Int): Difficulty {
    var level: Difficulty
    if (stars == 1) level = Difficulty.EASY
    else if (stars == 2) level = Difficulty.MEDIUM
    else level = Difficulty.HARD
    return level
}

// Expression style: the when IS the value. No var, nothing to forget, nothing to reassign later.
fun difficultyOf(stars: Int): Difficulty = when (stars) {
    1 -> Difficulty.EASY
    2 -> Difficulty.MEDIUM
    else -> Difficulty.HARD
}

// try is an expression too: the value of the try block, or the value of the catch block.
fun parseGrams(raw: String): Int = try {
    raw.toInt()
} catch (e: NumberFormatException) {
    -1
}

fun main() {
    for (stars in listOf(1, 2, 3)) {
        println("$stars stars -> ${difficultyOf(stars)} (statement version: ${difficultyStatement(stars)})")
    }
    println("parseGrams(\"250\") = ${parseGrams("250")}")
    println("parseGrams(\"25O\") = ${parseGrams("25O")}")      // typed with a letter O
}
