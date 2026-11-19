package workbench.ksp.app.l09

import java.lang.reflect.Field
import java.lang.reflect.Modifier
import java.util.concurrent.ConcurrentHashMap
import workbench.ksp.annotations.Inventory

// The card without code generation: unpack the box at the new house and look inside, while the program runs.
// Plain Java reflection (no kotlin-reflect), the way lesson 1 does it. @Inventory is kept at RUNTIME for this.

/** Naive: looks up and opens the fields again on every call. */
fun reflectionCard(thing: Any): String {
    val type = thing.javaClass
    require(type.isAnnotationPresent(Inventory::class.java)) { "${type.simpleName} has no @Inventory" }
    val fields = type.declaredFields.filter { !Modifier.isStatic(it.modifiers) && !it.isSynthetic }
    return type.simpleName + ": " + fields.joinToString(", ") { field ->
        field.isAccessible = true
        "${field.name}=${field.get(thing)}"
    }
}

/** Reflection's best shot: find and open each class's fields once, then reuse them. */
object CachedReflectionCards {
    private val fieldsByClass = ConcurrentHashMap<Class<*>, List<Field>>()

    fun card(thing: Any): String {
        val fields = fieldsByClass.computeIfAbsent(thing.javaClass) { type ->
            require(type.isAnnotationPresent(Inventory::class.java)) { "${type.simpleName} has no @Inventory" }
            type.declaredFields.filter { !Modifier.isStatic(it.modifiers) && !it.isSynthetic }.onEach { it.isAccessible = true }
        }
        return thing.javaClass.simpleName + ": " + fields.joinToString(", ") { "${it.name}=${it.get(thing)}" }
    }
}
