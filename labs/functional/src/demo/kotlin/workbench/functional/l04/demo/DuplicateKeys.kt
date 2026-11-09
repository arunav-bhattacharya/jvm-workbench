package workbench.functional.l04.demo

// Payment, Status and sampleDay are in SampleDay.kt, next to this file.
fun main() {
    val byMerchant = sampleDay.groupBy({ it.merchant }, { it.id })
    println("groupBy:      $byMerchant")
    println("map class:    ${byMerchant.javaClass.name}")

    // One value per key. acme and globex each have two payments. Which ones survive?
    println("associateBy:  ${sampleDay.associateBy({ it.merchant }, { it.id })}")

    // Counting per key in one pass, with no list per group.
    println("eachCount:    ${sampleDay.groupingBy { it.merchant }.eachCount()}")
}
