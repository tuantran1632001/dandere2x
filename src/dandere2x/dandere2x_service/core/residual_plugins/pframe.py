from dandere2x.dandere2x_service.dandere2x_service_context import Dandere2xServiceContext

# This is the inversion (sort of) function of what Dandere2x_cpp's pframe does (which is more commented).
# Dandere2x_CPP tells us how to take apart an image using vectors, this tells us how to put the upscaled version
# back together.
from dandere2x.dandere2xlib.wrappers.frame.frame import Frame, DisplacementVector


def pframe_image(context: Dandere2xServiceContext,
                 frame_next: Frame, frame_previous: Frame, frame_residual: Frame,
                 list_residual: list, list_predictive: list):
    """
    Create a new image using residuals and predictive vectors.
    Roughly, we can describe this method as

        frame_next = Transfrom(frame_previous, list_predictive) + frame_residuals.

    Although frame_residuals needs to also be transformed.

    Method Tasks:
        - Move blocks from frame_previous into frame_next using list_predictive
        - Move blocks from frame_residual into frame_next using list_residuals
    """

    # load context
    scale_factor = int(context.service_request.scale_factor)
    block_size = context.service_request.block_size
    bleed = context.bleed

    for x in range(int(len(list_predictive) / 4)):
        """
        Neat optimization trick - there's no need for pframe to copy over a block if the vectors
        point to the same place. In merge.py we just need to load the previous frame into the current frame
        to reach this optimization.
        """

        if int(list_predictive[x * 4 + 0]) != int(list_predictive[x * 4 + 1]) \
                or \
                int(list_predictive[x * 4 + 2]) != int(list_predictive[x * 4 + 3]):
            # load the vector
            vector = DisplacementVector(int(list_predictive[x * 4 + 0]),
                                        int(list_predictive[x * 4 + 1]),
                                        int(list_predictive[x * 4 + 2]),
                                        int(list_predictive[x * 4 + 3]))

            # apply the vector
            frame_next.copy_block(frame_previous, block_size * scale_factor,
                                  vector.x_2 * scale_factor,
                                  vector.y_2 * scale_factor,
                                  vector.x_1 * scale_factor,
                                  vector.y_1 * scale_factor)

    for x in range(int(len(list_residual) / 4)):
        # load every element in the list into a vector
        vector = DisplacementVector(int(list_residual[x * 4 + 0]),
                                    int(list_residual[x * 4 + 1]),
                                    int(list_residual[x * 4 + 2]),
                                    int(list_residual[x * 4 + 3]))

        # apply that vector to the image
        frame_next.copy_block(frame_residual, block_size * scale_factor,
                              (vector.x_2 * (block_size + bleed * 2)) * scale_factor + (bleed * scale_factor),
                              (vector.y_2 * (block_size + bleed * 2)) * scale_factor + (bleed * scale_factor),
                              vector.x_1 * scale_factor,
                              vector.y_1 * scale_factor)

    return frame_next
