package workbench.injector.l01

import com.google.devtools.ksp.ApiFeatures
import com.google.devtools.ksp.buildApiFeatures
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
import com.squareup.kotlinpoet.KModifier
import com.squareup.kotlinpoet.PropertySpec
import com.squareup.kotlinpoet.TypeSpec
import com.squareup.kotlinpoet.joinToCode
import com.squareup.kotlinpoet.ksp.toClassName
import com.squareup.kotlinpoet.ksp.writeTo

/** Registered in workbench/injector/l01/SymbolProcessorProvider, with the factory processor. */
class ComponentProcessorProvider : SymbolProcessorProvider {
    override fun create(environment: SymbolProcessorEnvironment): SymbolProcessor =
        ComponentProcessor(environment.codeGenerator, environment.logger)
}

/** For each @Component interface, `Generated<Name>`: the whole plan in one class, an aggregating output. */
class ComponentProcessor(
    private val codeGenerator: CodeGenerator,
    private val logger: KSPLogger,
) : SymbolProcessor {

    override val apiFeatures: ApiFeatures = buildApiFeatures {
        enableBackingFields = true
        enableContextParameters = true
    }

    // Given code: while the lab is unfinished this logs a warning and generates nothing.
    override fun process(resolver: Resolver): List<KSAnnotated> = try {
        writeComponents(resolver)
    } catch (e: NotImplementedError) {
        logger.warn("l01 not done yet: ${e.message?.substringAfter("not implemented: ")}")
        emptyList()
    }

    /** 1. Find and 2. Check (given), 3. Read with [creationOrder], 4. Write with [componentFile]. */
    fun writeComponents(resolver: Resolver): List<KSAnnotated> {
        val (ready, later) = resolver.getSymbolsWithAnnotation(COMPONENT).toList()
            .partition { it.validate(apiFeatures = apiFeatures) }
        for (component in ready.filterIsInstance<KSClassDeclaration>()) {
            val entryPoints = checkedEntryPoints(component) ?: continue
            val order = creationOrder(entryPoints, logger) ?: continue
            // aggregating: the plan is built from many files, and is redone whenever any file changes
            componentFile(component, entryPoints, order)
                .writeTo(codeGenerator, Dependencies(aggregating = true, component.containingFile!!))
        }
        return later
    }

    /** 2. Check: the component's entry points (abstract functions without parameters), or null after an error. */
    fun checkedEntryPoints(component: KSClassDeclaration): List<KSFunctionDeclaration>? {
        val name = component.simpleName.asString()
        if (component.classKind != ClassKind.INTERFACE) {
            logger.error("@Component goes on an interface that lists what the app asks for, but $name is not an interface", component)
            return null
        }
        val entryPoints = component.getAllFunctions().filter { it.isAbstract }.toList()
        val withParameters = entryPoints.filter { it.parameters.isNotEmpty() }
        for (e in withParameters) {
            logger.error("$name.${e.simpleName.asString()}() takes parameters, but a component function only names what it hands out", e)
        }
        return entryPoints.takeIf { withParameters.isEmpty() }
    }
}

/** `truck` for a singleton (a val, built once), `newTapeRoll` for anything else (a function, a new one per call). */
fun memberName(binding: Binding): String =
    if (binding.singleton) binding.name.replaceFirstChar(Char::lowercase) else "new${binding.name}"

/** How the component asks for one [binding]: `truck` or `newTapeRoll()`. */
fun reference(binding: Binding): CodeBlock =
    if (binding.singleton) CodeBlock.of("%N", memberName(binding)) else CodeBlock.of("%N()", memberName(binding))

/** `TruckFactory.create(driver)`: the factory call, with a reference for each constructor parameter. */
fun construct(binding: Binding): CodeBlock {
    val arguments = binding.parameters.map { reference(bindingFor(it.type.resolve())!!) }
    return CodeBlock.of("%T.create(%L)", factoryName(binding), arguments.joinToCode(", "))
}

/**
 * 4. Write: `Generated<Interface>.kt`, a class that implements the component interface.
 *  - each singleton in [order] becomes `private val truck: Truck = TruckFactory.create(driver)`, in that order;
 *  - every other binding becomes `private fun newTapeRoll(): TapeRoll = TapeRollFactory.create()`;
 *  - each entry point becomes `override fun movingDay(): MovingDay = movingDay` (or `= newMovingDay()`).
 * Use [memberName], [reference] and [construct]. File comment: "Generated by ComponentProcessor from <Interface>. Do not edit."
 */
fun componentFile(component: KSClassDeclaration, entryPoints: List<KSFunctionDeclaration>, order: List<Binding>): FileSpec {
    TODO("write Generated<Interface>.kt: a val per singleton in creation order, a new<Name>() function for the rest, an override per entry point")
}
