package workbench.generics

import java.lang.reflect.GenericArrayType
import java.lang.reflect.ParameterizedType
import java.lang.reflect.Type
import java.lang.reflect.TypeVariable
import java.lang.reflect.WildcardType

/**
 * Helpers for the variance tests.
 *
 * Kotlin keeps `out` and `in` in its own metadata, which plain Java reflection cannot read. But when
 * Kotlin compiles a parameter whose type is declared `out` (or `in`), it writes a Java wildcard into the
 * method's generic signature: a Kotlin `Feed<Payment>` parameter becomes `Feed<? extends Payment>` when
 * Feed is declared `out T`. These helpers read that signature, so a test can check your variance.
 */
object JavaSignatures {

    /** The generic Java type of parameter [index] of the method [method] in class [className]. */
    fun param(className: String, method: String, index: Int = 0): Type =
        Class.forName(className).declaredMethods.single { it.name == method }.genericParameterTypes[index]

    /** The generic Java parameter type rendered with simple names, such as `Feed<? extends Payment>`. */
    fun paramText(className: String, method: String, index: Int = 0): String = render(param(className, method, index))

    fun render(t: Type): String = when (t) {
        is ParameterizedType -> (t.rawType as Class<*>).simpleName + t.actualTypeArguments.joinToString(", ", "<", ">") { render(it) }
        is WildcardType -> when {
            t.lowerBounds.isNotEmpty() -> "? super " + render(t.lowerBounds[0])
            t.upperBounds[0] == Any::class.java -> "?"
            else -> "? extends " + render(t.upperBounds[0])
        }
        is GenericArrayType -> render(t.genericComponentType) + "[]"
        is TypeVariable<*> -> t.name
        is Class<*> -> if (t.isArray) render(t.componentType) + "[]" else t.simpleName
        else -> t.toString()
    }
}
