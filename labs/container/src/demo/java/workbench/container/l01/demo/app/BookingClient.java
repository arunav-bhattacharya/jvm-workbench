package workbench.container.l01.demo.app;

/** The box office's link to the city's booking service, which holds the seats for every theatre in town. */
public interface BookingClient {
    String reserve(String seat, long priceCents);
}
