package workbench.functional.l06.demo

data class Recipe(val name: String, val servings: Int, val grams: Int)

class TraySetup {
    var paper: Boolean = false
    var cookies: Int = 0
    override fun toString() = "TraySetup(paper=$paper, cookies=$cookies)"
}

// The two shapes, written by hand. A scope function is nothing more than this.
fun <T, R> T.myLet(block: (T) -> R): R = block(this)                 // object as `it`, returns the block's result
fun <T> T.myApply(block: T.() -> Unit): T { block(); return this }   // object as `this`, returns the object

fun main() {
    val recipe = Recipe("pancakes", 4, 200)

    // the same block, five ways: what comes back?
    println("let   -> ${recipe.let { it.servings * 2 }}")
    println("run   -> ${recipe.run { servings * 2 }}")
    println("with  -> ${with(recipe) { servings * 2 }}")
    println("also  -> ${recipe.also { it.servings * 2 }}")
    println("apply -> ${recipe.apply { servings * 2 }}")

    // the hand-written versions behave the same way
    println("myLet   -> ${recipe.myLet { it.servings * 2 }}")
    println("myApply -> ${TraySetup().myApply { paper = true; cookies = 12 }}")
}
