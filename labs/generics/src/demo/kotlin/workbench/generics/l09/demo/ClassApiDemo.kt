package workbench.generics.l09.demo

import kotlin.reflect.KClass
import kotlin.reflect.cast
import kotlin.reflect.safeCast

fun main() {
    val event: PaymentEvent = CardAuthorized("pay_1", 1_200)

    // 1. KClass <-> Class
    val k: KClass<CardAuthorized> = CardAuthorized::class
    val c: Class<CardAuthorized> = k.java
    println("k.java = ${c.simpleName}, c.kotlin == k: ${c.kotlin == k}, event.javaClass == c: ${event.javaClass == c}")

    // 2. checked is / as / as?
    println("isInstance: ${k.isInstance(event)}, cast(...).cents: ${k.cast(event).cents}, safeCast to RefundIssued: ${RefundIssued::class.safeCast(event)}")
    try {
        RefundIssued::class.cast(event)
    } catch (e: ClassCastException) {
        println("cast failed: ${e.message}")
    }

    // 3. names
    println("simpleName = ${k.simpleName}, qualifiedName = ${k.qualifiedName}")

    // 4. the primitive trap from lesson 8
    println("Int::class.java = ${Int::class.java}, Int::class.javaObjectType = ${Int::class.javaObjectType}")

    // Wrong move. Uncomment, predict the error, then run.
    // println(k.javaClass)
}
