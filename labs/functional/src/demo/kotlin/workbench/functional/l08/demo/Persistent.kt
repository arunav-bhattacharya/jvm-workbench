package workbench.functional.l08.demo

import kotlinx.collections.immutable.mutate
import kotlinx.collections.immutable.persistentListOf

fun main() {
    // the steps of a recipe, one edition at a time
    val v1 = persistentListOf("preheat the oven")
    val v2 = v1.adding("cream butter and sugar")             // a new list; v1 is untouched
    val v3 = v2.addingAll(listOf("beat in the eggs", "fold in the flour"))
    println("v1 = $v1")
    println("v2 = $v2")
    println("v3 = $v3")
    println("v1 is a ${v1.javaClass.simpleName}")

    // several changes at once, through a short-lived mutable builder
    val v4 = v3.mutate { steps ->
        steps.removeAt(0)
        steps += "bake for 25 minutes"
    }
    println("v4 = $v4")
    println("v3 = $v3 (unchanged)")

    // Uncomment the next line and run: the old name compiles with a deprecation warning,
    // returns a new list like adding, and here the new list is thrown away.
    // v1.add("lost")
    println("v1 = $v1 at the end")
}
