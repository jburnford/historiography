"""Explicit editorial decisions keyed to the frozen, numbered inventory.

This is a venue-scope screen, not an author survey or accepted person identity.
Every title was inspected; unassigned numbers must fail the final export.
"""
DECISIONS={}

def assign(category,numbers):
    for token in numbers.split():
        bounds=token.split('-');start=int(bounds[0]);end=int(bounds[-1])
        for number in range(start,end+1):
            if number in DECISIONS:raise ValueError(f'Duplicate decision: {number}')
            DECISIONS[number]={'category':category}

# 1–210: general/region history, historical subfields, and neighbouring venues.
assign('likely_core','''1 2 4 5 9 11 12 13 20 21 22 23 24 25 30 33 34 36 37 39 42 43 47 48 50 51
56 57 58 59 64 69 73 74 75 76 77 92 95 100 101 103 105 107 109 110 111 114 122 123 124 129 130 131
139 142 145 147 148 149 150 152 153 155 156 158 161 162 163 165 174 175 177 180 181 183 185 186 188 191 193 195 196 197 198 200 201 204 206 208 209''')
assign('mixed','''6 7 8 10 14 16 26 27 28 29 31 35 38 40 41 44 45 46 49 54 60 61 68 78 79 82 89 93 98 99 102 106 108 113 115 116 118 125 126 127 128 132 133 135 137 140 143 144 146 159 167 173 176 178 184 187 189 192 194 199 202 203 205 207 210''')
assign('other_primary_community','''3 15 17 18 19 32 52 53 55 62 63 65 66 67 70 71 72 80 81 83 84 85 86 87 88 90 91 94 96 97 104 112 117 119 120 121 134 136 138 141 151 154 157 160 164 166 168 169 170 171 172 179 182 190''')

# 211–420.
assign('likely_core','''211 212 214 217 220 221 222 223 225 226 229 230 235 240 241 243 245 246 248 250 251 252 253 254 256 258 259 261 262 264 267 269 271 274 275 276 282 286 287 288 289 290 291 292 293 294 295 297 298 299 300 301 303 304 305 307 308 309 310 312 313 314 315 316 317 318 319 320 321 322 323 324 327 328 329 331 333 334 337 339 340 341 343 344 347 349 350 357 359 360 361 363 364 365 369 370 372 377 379 382 383 384 387 388 390 394 395 401 402 404 406 407 409 413''')
assign('mixed','''215 216 218 233 236 237 238 244 247 255 257 268 270 272 279 280 281 285 296 302 306 311 325 326 330 332 335 342 346 351 352 353 355 356 362 366 367 371 373 375 376 378 380 381 385 386 389 396 400 403 405 408 410 412 414 417 420''')
assign('other_primary_community','''213 219 224 227 228 231 232 234 239 249 260 263 265 266 273 277 278 283 284 336 338 345 348 354 358 368 374 391 392 393 397 398 399 411 415 416 418 419''')
assign('uncertain','242')

# 421–630.
assign('likely_core','''421 422 423 425 426 428 429 430 431 432 435 437 441 443 445 449 452 453 454 455 457 458 460 462 463 466 468 473 474 475 477 480 481 487 491 492 493 494 495 496 497 498 499 500 502 505 507 508 509 510 514 515 516 517 519 520 522 524 526 527 528 529 531 536 537 540 543 546 547 549 551 552 554 555 556 557 561 563 564 565 566 568 570 573 574 579 580 586 589 590 594 595 598 600 603 606 607 608 609 614 615 616 618 619 621 624 625 629''')
assign('mixed','''424 427 433 436 438 447 451 456 459 461 465 467 469 471 476 482 484 488 489 490 501 503 504 506 511 512 513 523 525 530 533 534 538 541 542 545 550 558 559 560 567 569 571 572 576 577 578 581 582 583 585 587 593 601 604 605 610 612 613 617 620 628 630''')
assign('other_primary_community','''434 439 440 442 444 446 448 450 464 470 472 478 479 483 485 486 518 521 532 535 539 544 548 553 562 575 584 588 592 596 597 599 602 611 622 623 626 627''')
assign('uncertain','591')

# 631–819, including historical title contexts and the initial supplements.
assign('likely_core','''633 636 638 639 640 642 643 644 645 646 649 653 655 659 660 661 664 665 666 668 670 671 672 674 675 679 680 683 686 688 690 691 692 697 700 701 706 708 709 712 716 718 720 721 725 728 732 733 735 739 741 742 743 744 745 746 747 748 749 750 752 753 754 756 757 758 759 760 762 765 769 770 772 774 775 777 778 780 781 784 788 789 790 791 793 794 795 796 797 798 799 800-819''')
assign('mixed','''631 632 634 641 650 652 654 657 662 663 669 673 676 677 678 684 689 694 695 696 698 699 703 705 713 714 715 717 726 727 729 730 731 737 751 755 761 763 767 768 771 773 779 782 785 786 787''')
assign('other_primary_community','''635 637 647 648 651 656 658 667 681 682 685 687 693 702 704 707 710 711 719 722 723 724 734 736 738 740 764 766 776 783 792''')

# User's explicit exclusions are a separate scope policy, not erased source data.
def exclude(reason, numbers):
    for token in numbers.split():
        bounds = token.split('-')
        for number in range(int(bounds[0]), int(bounds[-1]) + 1):
            DECISIONS[number].setdefault('exclusions', []).append(reason)

exclude('archaeology', '''15 19 27 29 32 44 45 46 53 65 66 67 88 113 121
138 144 164 266 302 346 368 375 391 392 397 398 399 415 490 503 532 539
541 544 553 584 611 612 631 723 740''')
exclude('politics_or_political_science', '''63 85 86 87 90 97 98 117 141 151 157
170 172 173 179 187 190 231 265 273 342 374 405 412 416 439 448 469 470
480 562 581 582 583 585 626 627 628 634 635 685 687 735 776''')
exclude('general_area_studies', '''8 10 16 17 18 31 35 40 41 60 62 68 84 85 86
87 89 90 99 102 104 115 116 132 133 135 137 140 141 143 144 167 168 170 172
173 194 199 210 228 233 236 237 257 268 348 353 356 362 367 371 373 374 376
378 381 385 400 403 405 408 410 414 424 427 433 438 450 451 456 459 465 467
469 471 482 483 484 485 489 499 500 504 506 509 512 518 523 525 533 534 538
541 545 548 560 569 571 572 574 576 577 587 592 593 605 630 640 641 650 657
662 677 684 689 693 702 703 704 705 710 713 714 715 717 726 761 763 764 771
773 774 776''')

# Conservative second pass: these historical subjects have a less certain
# historian/historical-social-scientist majority. Keep available for review.
for number in (74, 193, 195, 246, 347, 388, 402, 422, 546, 624, 697):
    DECISIONS[number]['category'] = 'mixed'

def note(number, reason, url=None, basis='editorial_scope_assessment'):
    DECISIONS[number]['reason'] = reason
    DECISIONS[number]['evidence_basis'] = basis
    if url:
        DECISIONS[number]['scope_source_url'] = url

note(406, 'Retain: user confirms Journal of British Studies is overwhelmingly history. Regional coverage and the word Studies do not make it general area studies.',
     'https://www.cambridge.org/core/journals/journal-of-british-studies/information/about-this-journal',
     'user_editorial_correction_and_publisher_scope')
note(460, 'Retain as regional history: publisher frames coverage around political, economic, cultural and social history of Italy since 1700, while welcoming other disciplines.',
     'https://www.tandfonline.com/rmis', 'publisher_scope_checked')
note(574, 'Exclude under general area-studies policy: publisher scope combines Italian history with politics and contemporary social, economic and cultural life.',
     'https://www.cambridge.org/core/journals/modern-italy/information/about-this-journal', 'publisher_scope_checked')
note(480, 'Exclude: historical and geopolitical military affairs, explicitly serving security and military analysts; broader than military history.',
     'https://www.tandfonline.com/journals/fslv19', 'publisher_scope_checked')
note(500, 'Conservative area-studies exclusion: publisher includes Ottoman and republican Turkey scholarship across disciplinary boundaries; contributor majority has not been established.',
     'https://iupress.org/journals/jotsa/', 'publisher_scope_checked')
note(735, 'Exclude under political-science policy despite historical orientation: political and institutional development, published as political science.',
     'https://www.cambridge.org/core/journals/studies-in-american-political-development', 'publisher_scope_checked')
note(163, 'Retain comparative history and historical social science; interdisciplinary history, anthropology, sociology and political science readership does not itself disqualify it.',
     'https://www.cambridge.org/core/journals/comparative-studies-in-society-and-history/information/about-this-journal', 'publisher_scope_checked')
note(5, 'Retain accounting history as historical social science: focus on historical accounting thought, practice and institutions.',
     'https://www.tandfonline.com/journals/rabf21', 'publisher_scope_checked')
note(234, 'General accounting research community; historical research is not the defining remit.',
     'https://www.tandfonline.com/journals/rear20/about-this-journal', 'publisher_scope_checked')
note(399, 'Exclude archaeological science: scientific techniques applied to archaeology, aimed at archaeologists and scientific specialists.',
     'https://www.elleryfrahm.com/jasrep', 'editor_scope_checked')
note(14, 'Pilgrimage studies encompass history alongside art, literature, archaeology, anthropology and other fields; no historian majority established.',
     'https://www.caminodesantiago.gal/es/conocimiento-e-investigacion/ad-limina', 'publisher_scope_checked')
note(558, 'Interdisciplinary memory research includes psychology, sociology, literature, anthropology and history; no historian majority established.',
     'https://journals.sagepub.com/toc/mssa/1/1', 'publisher_editorial_checked')

for number, reason in {
    74: 'Natural-history history includes naturalists and specialist scientists; retain in mixed pool pending contributor review.',
    193: 'Diaspora history and social research overlap; historian majority uncertain.',
    195: 'Diplomatic history overlaps contemporary statecraft and international relations; hold outside core pending contributor review.',
    246: 'Historical fascism overlaps contemporary political research; hold in mixed pool.',
    347: 'Historical information studies overlap information science; current contributor balance needs checking.',
    388: 'History of astronomy includes astronomers and historians; contributor disciplinary balance uncertain.',
    402: 'Astronomical history and heritage includes professional and amateur astronomers; historian majority uncertain.',
    422: 'Early Christian studies includes historians, theologians and specialists in ancient texts; majority uncertain.',
    546: 'Historical religion overlaps anthropology and religious studies; contributor majority uncertain.',
    624: 'History of physics includes physicists as well as historians; contributor majority uncertain.',
    640: 'Conservative general regional-humanities exclusion: Russian history overlaps literature and philology; dedicated historian majority not established.',
    697: 'Settler colonial research spans history and contemporary political and social research; hold outside core.',
    242: 'History-of-psychology venue: insufficient scope evidence for a confident primary-community estimate.',
    591: 'Insufficient scope evidence in this screen; do not infer a historian majority from catalogue membership.',
}.items():
    note(number, reason)

assert set(DECISIONS) == set(range(1, 820))
assert DECISIONS[406]['category'] == 'likely_core'
assert not DECISIONS[406].get('exclusions')
