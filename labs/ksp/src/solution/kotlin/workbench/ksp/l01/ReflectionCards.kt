package workbench.ksp.l01

import java.lang.reflect.Modifier
import workbench.ksp.annotations.Inventory

// Part 2: the same card, worked out while the program runs. Reflection opens the object at run time: it asks
// the class for its annotations and its fields, then reads each field's value. No card is written by hand.

/**
 * The inventory card of [thing], by reflection: its class's simple name, a colon, then name=value for each
 * instance field, in the order `getDeclaredFields()` returns them (static and synthetic fields skipped).
 * Throws IllegalArgumentException("<Name> has no @Inventory note") when the class doesn't carry @Inventory.
 */
fun reflectionCard(thing: Any): String {
    val type = thing.javaClass
    // 1. the sticky note, looked up while the program runs (this is why @Inventory has RUNTIME retention)
    require(type.isAnnotationPresent(Inventory::class.java)) { "${type.simpleName} has no @Inventory note" }
    // 2. the fields: HotSpot returns them in declaration order, though the Javadoc promises no order at all
    val pairs = type.declaredFields
        .filter { !Modifier.isStatic(it.modifiers) && !it.isSynthetic }
        .joinToString(", ") { field ->
            field.isAccessible = true // the fields behind Kotlin properties are private
            "${field.name}=${field.get(thing)}"
        }
    return "${type.simpleName}: $pairs"
}
