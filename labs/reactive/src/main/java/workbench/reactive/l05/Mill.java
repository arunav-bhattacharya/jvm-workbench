package workbench.reactive.l05;

import reactor.core.publisher.Mono;

/** The mill's ordering service: a program on another computer that takes the bakery's flour orders. */
public interface Mill {
    /**
     * Sends one flour order to the mill. The Mono emits a confirmation, or fails with
     * {@link MillBusyException} (worth another try) or {@link OrderRefusedException} (final).
     */
    Mono<String> order(String orderId);
}
