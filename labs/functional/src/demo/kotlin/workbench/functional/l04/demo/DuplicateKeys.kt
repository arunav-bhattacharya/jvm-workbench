package workbench.functional.l04.demo

// Cookie, Status and sampleDay are in SampleDay.kt, next to this file.
fun main() {
    val byFlavor = sampleDay.groupBy({ it.flavor }, { it.id })
    println("groupBy:      $byFlavor")
    println("map class:    ${byFlavor.javaClass.name}")

    // One value per key. oat and chocolate each have two cookies. Which ones survive?
    println("associateBy:  ${sampleDay.associateBy({ it.flavor }, { it.id })}")

    // Counting per key in one pass, with no list per group.
    println("eachCount:    ${sampleDay.groupingBy { it.flavor }.eachCount()}")
}
