package workbench.injector.l01

import com.google.devtools.ksp.getConstructors
import com.google.devtools.ksp.isAbstract
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.symbol.KSFunctionDeclaration
import com.google.devtools.ksp.symbol.KSNode
import com.google.devtools.ksp.symbol.KSType
import com.google.devtools.ksp.symbol.KSValueParameter
import com.squareup.kotlinpoet.ClassName
import com.squareup.kotlinpoet.ksp.toClassName

// The plan, as the two processors of lesson 1 see it. Given code, except creationOrder (the Read move).

// The sticky notes, by their full names: getSymbolsWithAnnotation needs the full name, not the short one.
const val INJECT = "workbench.injector.annotations.Inject"
const val SINGLETON = "workbench.injector.annotations.Singleton"
const val COMPONENT = "workbench.injector.annotations.Component"

/** True if this symbol carries the annotation [qualifiedName]. Compares the short name first, which is cheap,
 *  and resolves the annotation's type only when the short name matches. */
fun KSAnnotated.hasAnnotation(qualifiedName: String): Boolean = annotations.any {
    it.shortName.asString() == qualifiedName.substringAfterLast('.') &&
        it.annotationType.resolve().declaration.qualifiedName?.asString() == qualifiedName
}

/**
 * One line of the plan: how to get one kind of thing. In this lesson every binding is a class with an @Inject
 * constructor, and the constructor's parameters are what the class needs (its dependencies).
 */
class Binding(val declaration: KSClassDeclaration, val constructor: KSFunctionDeclaration) {
    val className: ClassName = declaration.toClassName()
    val name: String = className.simpleName
    val key: String = declaration.qualifiedName!!.asString()
    /** @Singleton: one for the whole day. Otherwise a new one for every request. */
    val singleton: Boolean = declaration.hasAnnotation(SINGLETON)
    val parameters: List<KSValueParameter> get() = constructor.parameters
    override fun toString() = name
}

/** The constructor the plan calls: the primary one when the class carries @Inject, else the one marked @Inject. */
fun injectConstructorOf(cls: KSClassDeclaration): KSFunctionDeclaration? =
    if (cls.hasAnnotation(INJECT)) cls.primaryConstructor
    else cls.getConstructors().firstOrNull { it.hasAnnotation(INJECT) }

/** The binding for [type], or null when nobody provides it (it is not a class with an @Inject constructor). */
fun bindingFor(type: KSType): Binding? {
    val cls = type.declaration as? KSClassDeclaration ?: return null
    if (cls.classKind != ClassKind.CLASS || cls.isAbstract()) return null
    val constructor = injectConstructorOf(cls) ?: return null
    return Binding(cls, constructor)
}

/**
 * 3. Read: every binding the component needs in order to hand out its [entryPoints], each one placed after
 * everything its constructor asks for. Walk depth first from each entry point's return type and add a binding
 * when you leave it (post-order), once. When nobody provides a type, report it with [logger] on the parameter
 * (or entry point) that asks for it, keep walking to find any others, and return null at the end.
 *
 * Message: "Truck needs Driver, but nobody provides Driver. Add @Inject to its constructor."
 * For an entry point the one who needs it is "MovingDayComponent.movingDay()".
 *
 * Lesson 2 adds what this walk can't do yet: the whole path in the message, and cycles.
 */
fun creationOrder(entryPoints: List<KSFunctionDeclaration>, logger: KSPLogger): List<Binding>? {
    val order = LinkedHashMap<String, Binding>()     // key to binding, in creation order
    var missing = false

    fun need(type: KSType, who: String, where: KSNode): Binding? = bindingFor(type).also {
        if (it == null) {
            val wanted = type.declaration.simpleName.asString()
            logger.error("$who needs $wanted, but nobody provides $wanted. Add @Inject to its constructor.", where)
            missing = true
        }
    }

    fun visit(binding: Binding) {
        if (binding.key in order) return                                   // already in the plan: shared, not rebuilt
        for (p in binding.parameters) need(p.type.resolve(), binding.name, p)?.let(::visit)
        order[binding.key] = binding                                       // post-order: after everything it needs
    }

    for (e in entryPoints) {
        val who = "${e.parentDeclaration?.simpleName?.asString()}.${e.simpleName.asString()}()"
        need(e.returnType!!.resolve(), who, e)?.let(::visit)
    }
    return if (missing) null else order.values.toList()
}
