package workbench.injector.l02.demo

import java.lang.reflect.Method
import java.lang.reflect.Parameter
import workbench.injector.annotations.Inject
import workbench.injector.annotations.Named
import workbench.injector.annotations.Provides
import workbench.injector.annotations.Singleton

/**
 * The plan worked out on the street: a container that reads the sticky notes by reflection while the program
 * runs, and builds what you ask for on the spot. Naive on purpose: it checks nothing before you ask.
 */
class ReflectionContainer(vararg modules: Any) {

    private data class Key(val type: Class<*>, val name: String?)

    private val provides = HashMap<Key, Pair<Any, Method>>()
    private val singletons = HashMap<Key, Any>()

    init {
        for (module in modules) {
            for (method in module.javaClass.declaredMethods) {
                if (!method.isAnnotationPresent(Provides::class.java)) continue
                // a second @Provides for the same key quietly replaces the first
                provides[Key(method.returnType, method.getAnnotation(Named::class.java)?.value)] = module to method
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

    private fun argumentsFor(parameters: Array<Parameter>): Array<Any> =
        Array(parameters.size) { i -> get(Key(parameters[i].type, parameters[i].getAnnotation(Named::class.java)?.value)) }
}
