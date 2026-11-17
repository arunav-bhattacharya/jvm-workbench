package workbench.bytecode.l02

import java.lang.reflect.Modifier

// Five Kotlin shapes. main() prints the JVM members of each class, close to what `javap -p` shows.

data class Scene(val title: String, val minutes: Int = 0)

class Actor(val name: String) {
    var lines: Int = 0
        private set                               // a getter, and no setter at all
    val isSpeaking: Boolean get() = lines > 0
    lateinit var dressingRoom: String             // a public field, plus getter and setter

    companion object {
        const val MAX_ROLES = 3                   // public static final on Actor
        val HOME_STAGE = "Main Stage"             // private static on Actor, getter on Companion
        @JvmStatic fun hire(name: String) = Actor(name)     // static on Actor AND on Companion
        fun guest(name: String) = Actor(name)               // only on Companion
    }
}

object Company {
    val actors = mutableListOf<Actor>()
}

fun greet(name: String = "Ana", punct: Char = '!') = "Hello $name$punct"

fun main() {
    val classes = listOf(
        Scene::class.java, Actor::class.java, Actor.Companion::class.java,
        Company::class.java, Class.forName("workbench.bytecode.l02.KotlinShapesKt"),
    )
    for (c in classes) {
        println("${Modifier.toString(c.modifiers)} class ${c.name}")
        c.declaredFields.sortedBy { it.name }.forEach {
            println("    field  ${Modifier.toString(it.modifiers)} ${it.type.simpleName} ${it.name}")
        }
        c.declaredConstructors.forEach { k ->
            println("    ctor   (${k.parameterTypes.joinToString { it.simpleName }})" + if (k.isSynthetic) " synthetic" else "")
        }
        c.declaredMethods.sortedBy { it.name }.forEach { m ->
            println("    method ${Modifier.toString(m.modifiers)} ${m.name}(${m.parameterTypes.joinToString { it.simpleName }})")
        }
    }
}
