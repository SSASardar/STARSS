command_centre.o: src/command_centre.c include/control_centre.h \
  include/radars.h include/common.h include/vertical_profiles.h \
  include/material_coords_raincell.h include/spatial_coords_raincell.h
common.o: src/common.c include/common.h
main.o: src/main.c include/material_coords_raincell.h \
  include/spatial_coords_raincell.h include/common.h
material_coords_raincell.o: src/material_coords_raincell.c \
  include/material_coords_raincell.h include/common.h
processing.o: src/processing.c include/processing.h include/common.h \
  include/radars.h include/material_coords_raincell.h \
  include/spatial_coords_raincell.h include/vertical_profiles.h
radars.o: src/radars.c include/radars.h include/common.h \
  include/spatial_coords_raincell.h include/material_coords_raincell.h \
  include/vertical_profiles.h
spatial_coords_raincell.o: src/spatial_coords_raincell.c \
  include/spatial_coords_raincell.h include/common.h \
  include/material_coords_raincell.h
true_vertical_profile.o: src/true_vertical_profile.c \
  include/true_vertical_profile.h include/material_coords_raincell.h \
  include/common.h
vertical_profiles.o: src/vertical_profiles.c include/vertical_profiles.h
