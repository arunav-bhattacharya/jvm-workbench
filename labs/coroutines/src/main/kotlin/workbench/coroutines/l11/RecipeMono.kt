package workbench.coroutines.l11

import kotlinx.coroutines.runBlocking
import reactor.core.publisher.Mono

/**
 * The recipe as a Reactor Mono, for a caller written with Reactor.
 *
 * Rules: the Mono is cold (nothing runs until someone subscribes, and each subscription looks
 * the recipe up again), it completes empty when [RecipeBook.recipe] returns null, and disposing
 * the subscription cancels the coroutine.
 *
 * Bug: runBlocking looks the recipe up the moment recipeMono is called, blocking the caller's
 * thread, before anyone subscribes, and only once however many subscribers come. Disposing a
 * subscription can't cancel a lookup that has already finished.
 */
fun recipeMono(book: RecipeBook, dish: String): Mono<Recipe> =
    Mono.justOrEmpty(runBlocking { book.recipe(dish) })
