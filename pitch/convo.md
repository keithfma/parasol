# Rationale-in-Progress for *Parasol* Project

## Idea

Incorporate sun/shade conditions into a routing application to allow users to
remain as comfortable as possible while going from A to B.

## **Co**ntext

*Who are the people with an interest in the results of this project? What are
they generally trying to achieve? What work, generally, is the project going to
be furthering?*

This project is aimed at people who use mapping applications for travel
directions, especially on foot or by bike. The user goal is to get to some
destination in the best way possible. *Best* is usually defined in terms of
travel time (and perhaps route complexity). The new contribution here is to
include the comfort of the user as well.

## **N**eed

*What are the specific needs that could be fixed by intelligently using the
data? These needs should be presetned in terms that are meaningful to the
organization. If our method will be to build a model, the need is not to build
a model. The need is to solve the porblem that having a model will solve.*

The need is simple: stay cool on hot days, and warm on cool days by choosing
routes that make best use of the sun and shade provided by the natural and
built environment. People do this naturally as a matter of course, for example,
switching to the shady or sunny side of the road during thier walk, or choosing
one turn over another. The benefit of using an application is that it can look
ahead farther than the user can see, and may know about alternative routes that
the user does not.

This need is relatively weak, in that I would not expect user's to break do
extra work to get this information. Luckily, the need can be addressed within
existing route finding applications, as a simple add-on feature that requires
little or no user input.

## **V**ision

*The vision is a glimpse of what it will look like to meet the need with data.
It could consist of a mockup describing the intended results, or a sketch of
the argument that we're going to make, or some particular questions that
narrowly focus our aims.*

The vision is a simple modification of existing directions applications. When
presenting routes to the user, it is customary to present several alternative
routes and let the user decide. The *Parasol* feature would (1) color the route
lines based on sun (yellow) and (shade), (2) summarize both time and
time-in-sun along each route, and (3) provide a switch or slider that users can
use to select their preference for sun or shade.

This could be implemented as a new feature in existing applications (if they
would let me) or as a stand-alone application.

## **O**utcome

*We need to understand how the work will actually make it back to the rest of
the orgainization and what will happen once it is there. How will it be userd?
How will it be integrated into the organization? Who will own its integration?
Who will use it? In the end, how will it success be measured?*

This idea is user-facing, to deployed as a feature in an existing application
or as a stand-alone application. I would measure success by retrospectively
analyzing the percentage of users that take advantage of the feature.
