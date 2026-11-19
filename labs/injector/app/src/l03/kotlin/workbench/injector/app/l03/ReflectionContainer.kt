package workbench.injector.app.l03

import java.lang.reflect.Method
import java.lang.reflect.Parameter
import java.lang.reflect.ParameterizedType
import java.lang.reflect.Type
import java.lang.reflect.WildcardType
import workbench.injector.annotations.Inject
import workbench.injector.annotations.Named
import workbench.injector.annotations.Provides
import workbench.injector.annotations.Singleton

/**
 * The plan worked out on the street, for comparison: it reads the same sticky notes by reflection while the
 * program runs and builds what you ask for on the spot, Lazy<T> and () -> T included. It checks nothing in
 * advance (see cap5-02), and it is only here so that StartupRace has something to race against.
 */
class ReflectionContainer(vararg modules: Any) {

    private data class Key(val type: Class<*>, val name: String?)

    private val provides = HashMap<Key, Pair<Any, Method>>()
    private val singletons = HashMap<Key, Any>()

    init {
        for (module in modules) {
            for (method in module.javaClass.declaredMethods) {
                if (method.isAnnotationPresent(Provides::class.java)) {
                    provides[Key(method.returnType, method.getAnnotation(Named::class.java)?.value)] = module to method
                }
            }
        }
    }

    fun <T : Any> get(type: Class<T>): T = type.cast(get(Key(type, null)))

    private fun get(key: Key): Any {
        singletons[key]?.let { return it }
        val provider = provides[key]
        val made = provider?.let { (module, method) -> method.invoke(module, *argumentsFor(method.parameters)) }
            ?: construct(key.type)
        val singleton = provider?.second?.isAnnotationPresent(Singleton::class.java)
            ?: key.type.isAnnotationPresent(Singleton::class.java)
        if (singleton) singletons[key] = made
        return made
    }

    private fun construct(type: Class<*>): Any {
        val constructor = type.constructors.singleOrNull { it.isAnnotationPresent(Inject::class.java) }
            ?: type.constructors.singleOrNull()?.takeIf { type.isAnnotationPresent(Inject::class.java) }
            ?: throw IllegalStateException("no @Inject constructor on ${type.name}")
        return constructor.newInstance(*argumentsFor(constructor.parameters))
    }

    private fun argumentsFor(parameters: Array<Parameter>): Array<Any> = Array(parameters.size) { i ->
        val p = parameters[i]
        val name = p.getAnnotation(Named::class.java)?.value
        when (p.type) {
            Lazy::class.java -> lazy { get(Key(innerClass(p.parameterizedType), name)) }
            Function0::class.java -> { -> get(Key(innerClass(p.parameterizedType), name)) }
            else -> get(Key(p.type, name))
        }
    }

    /** `Lazy<GpsUnit>` gives GpsUnit: the generic type survives in the class file's signature. */
    private fun innerClass(type: Type): Class<*> = when (val argument = (type as ParameterizedType).actualTypeArguments[0]) {
        is Class<*> -> argument
        is WildcardType -> argument.upperBounds[0] as Class<*>
        else -> error("can't read the type argument of $type")
    }
}
