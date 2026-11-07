package workbench.generics.l09.demo

import kotlin.reflect.KClass
import kotlin.reflect.KType
import kotlin.reflect.typeOf

fun main() {
    // 1. Three different objects.
    val k: KClass<String> = String::class         // Kotlin's object for a class
    val c: Class<String> = String::class.java     // Java's object for the same class
    val t: KType = typeOf<List<String>?>()         // a full type: class, arguments, nullability
    println("KClass: $k")
    println("Class:  $c")
    println("KType:  $t")

    // 2. Different types, one class.
    println("ArrayList<String> and ArrayList<Int> share a class: ${ArrayList<String>()::class == ArrayList<Int>()::class}")
    println("String? is backed by the class String: ${typeOf<String?>().classifier == String::class}")
    println("but the types differ: ${typeOf<String>() == typeOf<String?>()}, ${typeOf<List<String>>() == typeOf<List<Int>>()}")

    // 3. What a KType knows that a KClass doesn't.
    println("classifier is List::class: ${t.classifier == List::class}, arguments: ${t.arguments.size}, nullable: ${t.isMarkedNullable}")
}
