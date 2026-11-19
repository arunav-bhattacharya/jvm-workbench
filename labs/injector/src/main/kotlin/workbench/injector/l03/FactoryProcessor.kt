package workbench.injector.l03

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
import com.google.devtools.ksp.isAbstract
import com.google.devtools.ksp.isPrivate
import com.google.devtools.ksp.processing.CodeGenerator
import com.google.devtools.ksp.processing.Dependencies
import com.google.devtools.ksp.processing.KSPLogger
import com.google.devtools.ksp.processing.Resolver
import com.google.devtools.ksp.processing.SymbolProcessor
import com.google.devtools.ksp.processing.SymbolProcessorEnvironment
import com.google.devtools.ksp.processing.SymbolProcessorProvider
import com.google.devtools.ksp.symbol.ClassKind
import com.google.devtools.ksp.symbol.KSAnnotated
import com.google.devtools.ksp.symbol.KSClassDeclaration
import com.google.devtools.ksp.symbol.KSFunctionDeclaration
import com.google.devtools.ksp.validate
import com.squareup.kotlinpoet.ClassName
import com.squareup.kotlinpoet.CodeBlock
import com.squareup.kotlinpoet.FileSpec
import com.squareup.kotlinpoet.FunSpec
import com.squareup.kotlinpoet.ParameterSpec
import com.squareup.kotlinpoet.TypeSpec
import com.squareup.kotlinpoet.joinToCode
import com.squareup.kotlinpoet.ksp.toTypeName
import com.squareup.kotlinpoet.ksp.writeTo

/** Registered in workbench/injector/l03/SymbolProcessorProvider, with the component processor. */
class FactoryProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        FactoryProcessor(environment.codeGenerator, environment.logger)
}

// Given code: the factory processor from lessons 1 and 2, unchanged.

/** One factory per class with an @Inject constructor: an isolating output, made from that class's file alone. */
class FactoryProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
) : SymbolProcessor {

    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    // Given code: while the lab is unfinished this logs a warning and generates nothing,
    // so a real build with -Pmine still runs.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        writeFactories(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l03 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    /** 1. Find, 2. Check (given), then 4. Write one factory per class with [factoryFile]. */
    fun writeFactories(resolver: Resolver): List<KSAnnotated> {
        val (ready, later) = resolver.getSymbolsWithAnnotation(INJECT).toList()
            .partition { it.validate(apiFeatures = apiFeatures) }
        val seen = mutableSetOf<Key>()
        for (symbol in ready) {
            val binding = checked(symbol) ?: continue
            if (!seen.add(binding.key)) continue                     // @Inject on the class and on its constructor
            // isolating: this factory depends on the class's own file, and on nothing else
            factoryFile(binding).writeTo(codeGenerator, Dependencies(aggregating = false, binding.declaration.containingFile!!))
        }
        return later
    }

    /** 2. Check: the binding an @Inject note points at, or null after an error on the exact symbol. */
    fun checked(symbol: KSAnnotated): ConstructorBinding? {
        val cls = when (symbol) {
            is KSClassDeclaration -> symbol
            is KSFunctionDeclaration -> symbol.parentDeclaration as? KSClassDeclaration ?: return null
            else -> return null
        }
        val name = cls.simpleName.asString()
        val constructor = if (symbol is KSFunctionDeclaration) symbol else cls.primaryConstructor
        val problem = when {
            cls.classKind != ClassKind.CLASS -> "@Inject goes on a class the plan can build, but $name is ${kindOf(cls)}"
            cls.isAbstract() -> "@Inject goes on a class the plan can build, but $name is abstract"
            constructor == null -> "$name has no primary constructor: put @Inject on the constructor the plan should call"
            constructor.isPrivate() -> "$name's @Inject constructor is private, so its factory can't call it"
            else -> null
        }
        if (problem != null) {
            logger.error(problem, cls)
            return null
        }
        return ConstructorBinding(cls, constructor!!)
    }

    private fun kindOf(cls: KSClassDeclaration) = when (cls.classKind) {
        ClassKind.INTERFACE -> "an interface"
        ClassKind.OBJECT -> "an object (there is only one already)"
        ClassKind.ENUM_CLASS -> "an enum class"
        else -> "not a class"
    }
}

/** The factory's name, next to the class: `movemate.Driver` gets `movemate.DriverFactory`. */
fun factoryName(binding: ConstructorBinding): ClassName =
    ClassName(binding.className.packageName, "${binding.name}Factory")

/**
 * 4. Write: `<Name>Factory.kt` with one object and one function that takes what the constructor takes:
 *
 *     public object DriverFactory {
 *       public fun create(route: Route): Driver = Driver(route)
 *     }
 *
 * File comment: "Generated by FactoryProcessor from Driver. Do not edit."
 */
fun factoryFile(binding: ConstructorBinding): FileSpec {
    val parameters = binding.parameters.map { ParameterSpec(it.name!!.asString(), it.type.toTypeName()) }
    val create = FunSpec.builder("create")
        .addParameters(parameters)
        .returns(binding.className)
        .addStatement("return %T(%L)", binding.className, parameters.map { CodeBlock.of("%N", it) }.joinToCode(", "))
        .build()
    val factory = factoryName(binding)
    return FileSpec.builder(factory)
        .addFileComment("Generated by FactoryProcessor from %L. Do not edit.", binding.name)
        .addType(TypeSpec.objectBuilder(factory).addFunction(create).build())
        .build()
}
