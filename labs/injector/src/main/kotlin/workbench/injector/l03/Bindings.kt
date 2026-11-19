package workbench.injector.l03

import com.google.devtools.ksp.getConstructors
import com.google.devtools.ksp.isAbstract
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.symbol.KSFunctionDeclaration
import com.google.devtools.ksp.symbol.KSNode
import com.google.devtools.ksp.symbol.KSType
import com.google.devtools.ksp.symbol.KSValueParameter
import com.squareup.kotlinpoet.ClassName
import com.squareup.kotlinpoet.ksp.toClassName

// Given code: lesson 2's model, plus how a parameter asks for its dependency (Kind), with requestOf to write.

const val INJECT = "workbench.injector.annotations.Inject"
const val SINGLETON = "workbench.injector.annotations.Singleton"
const val COMPONENT = "workbench.injector.annotations.Component"
const val MODULE = "workbench.injector.annotations.Module"
const val PROVIDES = "workbench.injector.annotations.Provides"
const val NAMED = "workbench.injector.annotations.Named"

/** True if this symbol carries the annotation [qualifiedName] (short name first, which is cheap, then resolved). */
fun KSAnnotated.hasAnnotation(qualifiedName: String): Boolean = annotations.any {
    it.shortName.asString() == qualifiedName.substringAfterLast('.') &&
        it.annotationType.resolve().declaration.qualifiedName?.asString() == qualifiedName
}

/** The value of this symbol's @Named qualifier, or null if it has none. */
fun KSAnnotated.qualifier(): String? = annotations.firstOrNull {
    it.shortName.asString() == "Named" && it.annotationType.resolve().declaration.qualifiedName?.asString() == NAMED
}?.arguments?.firstOrNull()?.value as? String

/**
 * What a binding answers to: a type, plus the qualifier that tells two bindings of one type apart.
 * Prints the way the messages need it: `Driver`, or `@Named("highway") Route`.
 */
data class Key(val type: String, val qualifier: String? = null) {
    override fun toString(): String =
        (if (qualifier != null) "@Named(\"$qualifier\") " else "") + type.substringAfterLast('.')
}

/** The key for a request of [type] made by [annotated] (a parameter or a function, which may carry @Named). */
fun keyOf(type: KSType, annotated: KSAnnotated): Key =
    Key(type.declaration.qualifiedName?.asString() ?: type.toString(), annotated.qualifier())

/** How a parameter asks for what it needs. */
enum class Kind {
    /** `gps: GpsUnit`: built before the one who asks. */
    DIRECT,
    /** `gps: Lazy<GpsUnit>`: built on the first `gps.value`, then the same one every time. */
    LAZY,
    /** `newTape: () -> TapeRoll`: one more on every call (or the shared one, for a singleton). */
    PROVIDER,
}

/**
 * 3. Read: how a parameter of [type] asks, and for what. `Lazy<GpsUnit>` is (LAZY, GpsUnit), `() -> TapeRoll`
 * is (PROVIDER, TapeRoll), and anything else is (DIRECT, the type itself).
 * `kotlin.Lazy` is a class like any other: compare its qualified name. A function type with no parameters is
 * `kotlin.Function0`, and its one type argument is what it returns. Resolve a type argument with `type!!.resolve()`.
 */
fun requestOf(type: KSType): Pair<Kind, KSType> {
    TODO("unwrap Lazy<T> into (LAZY, T) and () -> T into (PROVIDER, T); anything else is (DIRECT, the type)")
}

/** One thing a binding (or an entry point) asks for; [node] is where it asks, for the error's file and line. */
class Dependency(val key: Key, val type: KSType, val node: KSNode, val kind: Kind = Kind.DIRECT)

private fun KSValueParameter.asDependency(): Dependency {
    val (kind, wanted) = requestOf(type.resolve())
    return Dependency(keyOf(wanted, this), wanted, this, kind)
}

/** One line of the plan: how to get one kind of thing. Its [toString] is its key, which the messages print. */
sealed class Binding {
    abstract val key: Key
    abstract val singleton: Boolean
    abstract val dependencies: List<Dependency>
    /** The type it builds, for the generated code. */
    abstract val className: ClassName
    /** Where the binding is declared, for an error's file and line. */
    abstract val node: KSNode
    /** How a message names it: `RouteModule.highway()` or `Route's @Inject constructor`. */
    abstract val origin: String
    override fun toString(): String = key.toString()
}

/** A class with an @Inject constructor. */
class ConstructorBinding(val declaration: KSClassDeclaration, val constructor: KSFunctionDeclaration) : Binding() {
    override val className: ClassName = declaration.toClassName()
    val name: String = className.simpleName
    override val key = Key(declaration.qualifiedName!!.asString())
    override val singleton = declaration.hasAnnotation(SINGLETON)
    override val dependencies: List<Dependency> by lazy { constructor.parameters.map { it.asDependency() } }
    override val node: KSNode get() = declaration
    override val origin: String get() = "$name's @Inject constructor"
    val parameters: List<KSValueParameter> get() = constructor.parameters
}

/** A @Provides function in a @Module object: for things you can't put @Inject on. */
class ProvidesBinding(val module: KSClassDeclaration, val function: KSFunctionDeclaration) : Binding() {
    val type: KSType = function.returnType!!.resolve()
    override val className: ClassName = (type.declaration as KSClassDeclaration).toClassName()
    override val key = keyOf(type, function)
    override val singleton = function.hasAnnotation(SINGLETON)
    override val dependencies: List<Dependency> by lazy { function.parameters.map { it.asDependency() } }
    override val node: KSNode get() = function
    override val origin: String = "${module.simpleName.asString()}.${function.simpleName.asString()}()"
}

/** One function of the component interface: something the app asks for. */
class EntryPoint(val function: KSFunctionDeclaration) {
    val type: KSType = function.returnType!!.resolve()
    val key: Key = keyOf(type, function)
    val name: String = "${function.parentDeclaration?.simpleName?.asString()}.${function.simpleName.asString()}()"
}

/** The constructor the plan calls: the primary one when the class carries @Inject, else the one marked @Inject. */
fun injectConstructorOf(cls: KSClassDeclaration): KSFunctionDeclaration? =
    if (cls.hasAnnotation(INJECT)) cls.primaryConstructor
    else cls.getConstructors().firstOrNull { it.hasAnnotation(INJECT) }

/** The @Inject-constructor binding for [type], or null if it is not a class with an @Inject constructor. */
fun constructorBinding(type: KSType): ConstructorBinding? {
    val cls = type.declaration as? KSClassDeclaration ?: return null
    if (cls.classKind != ClassKind.CLASS || cls.isAbstract()) return null
    val constructor = injectConstructorOf(cls) ?: return null
    return ConstructorBinding(cls, constructor)
}
