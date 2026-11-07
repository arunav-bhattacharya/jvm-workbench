package workbench.generics.l09.demo

import java.lang.reflect.ParameterizedType
import java.lang.reflect.Type
import kotlin.reflect.KType
import kotlin.reflect.javaType
import kotlin.reflect.typeOf

/** A super type token written in Kotlin: the anonymous subclass remembers its superclass's type argument. */
abstract class TypeRef<T> {
    val type: Type = (javaClass.genericSuperclass as ParameterizedType).actualTypeArguments[0]
}

/** typeOf through a reified T keeps the whole type. T::class here would keep only the class. */
inline fun <reified T> tokenOf(): KType = typeOf<T>()

@OptIn(ExperimentalStdlibApi::class)                  // KType.javaType still needs the opt-in in 2.4.21
fun main() {
    val t = typeOf<Map<String, List<Int>>>()
    println("typeOf:           $t")
    println("arguments:        ${t.arguments.size}, second is ${t.arguments[1]}")
    println("javaType:         ${t.javaType}")
    println("tokenOf<List<String>>() == typeOf<List<String>>(): ${tokenOf<List<String>>() == typeOf<List<String>>()}")
    println("List<String> == List<Int> as KTypes: ${typeOf<List<String>>() == typeOf<List<Int>>()}")
    println("super type token: ${object : TypeRef<Map<String, List<Int>>>() {}.type}")

    // Wrong move. Uncomment, predict the error, then run.
    // val k = List<String>::class
}
